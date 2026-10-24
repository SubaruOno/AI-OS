#!/usr/bin/env python3
"""今大会の名簿（現地の表記）と、WBSCの登録名簿（ローマ字）を結ぶ案を作る。

collect.py --rosters が書いた rosters.csv（playerid つき）と、手で集めた
07_出場選手情報/今大会_発表名簿.csv を、チームごとに名前で突き合わせる。
名簿の表記はチームによって違うので、名前の比べ方を3通り持つ。
    韓国   ハングルを1音ずつローマ字（文化観光部式）にして比べる。Kim/Gim、Lee/Yi、
           eo/u、oo/u、g/k などのゆれはならす。名簿_読み.csv のカタカナは使わない
           （カタカナにすると ㅓ/ㅗ やパッチムの区別が消えるので、ハングルから直接読む）
    台湾   漢字を中国語の読み（macOS の変換）にし、ウェード式・漢語拼音・通用拼音の
           どれかで一致するかを見る。曾・柏 など名前で読みの変わる字は両方試す
    ほか   スペイン語などの綴りのゆれ（アクセント、y/i、qu/k、v/b、h など）をならし、
           名と第1姓で比べる（2つ目の姓と2つ目の名は、片方にしかなくてもよい）
「確認済み」の候補にするのは、次の3つをすべて満たす組だけ。
    - 姓と名がどちらも一致する（または、名簿照合.csv で結んだ過去の記録と登録名・生年が同じ）
    - 名簿の1人に登録の1人だけが一致し、その登録の1人にも名簿の1人だけが一致する
    - 守備（投手・捕手・内野・外野）、投打、生年、背番号のうち、両方に書いてあるものが食い違わない
名前が近いだけの組、食い違いのある組、候補が2人以上いる組は、人が見る一覧（要確認）に回し、
自動では結ばない。

    python3 roster_match.py              案を作り、名簿照合.csv に足す行を見せる（何も書き換えない）
    python3 roster_match.py --apply      同じ案を作り、見せた行を名簿照合.csv（と同一人物.csv）に足す
    python3 roster_match.py --event u23-wc-2024 --announced <当時の発表名簿.csv> --match <照合表>
                                         過去の大会で試す（--match は空のファイルか、ないパスでよい）
    python3 roster_match.py --selftest   名前の比べ方の決まりを確かめる（通信しない）

書き出すもの（既定は 05_収集データ/<大会キー>/。0行なら前回のものをゴミ箱へ送る）
    名簿照合_案.csv       名簿照合.csv に足す行（確認済み）
    名簿照合_要確認.csv   人が見る一覧。近い候補・食い違い・名簿だけ・登録だけの選手
    同一人物_案.csv       名簿の選手が過去の記録と結ばれていて、今大会の登録名だと別の人の鍵に
                          なる組。今大会の記録が出た選手だけ（記録がないと build_site.py が注意を出すため）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from io import StringIO
from pathlib import Path

import build_report as br
import collect
import site_logic as sl

CURRENT = "u23-wc-2026"
INFO = br.DATA_ROOT.parent / "07_出場選手情報"
SITE_INFO = INFO / "サイト用"
MATCH_FIELDS = ["team", "roster_name", "playerid", "wbsc_name", "birth", "match", "evidence"]
SAME_FIELDS = ["team", "keep_playerid", "merge_playerid", "evidence"]
FULL, NEAR = "一致", "近い"


# ---------------------------------------------------------------- 文字の下ごしらえ


def plain(text) -> str:
    """アクセントを外して小文字にする。ハングルは字母に分かれるので、ローマ字にだけ使う。"""
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def letters(text) -> str:
    """ローマ字の文字だけを小文字で（空白・ハイフン・アクセントを外す）。"""
    return re.sub(r"[^a-z]", "", plain(text))


def has_hangul(text: str) -> bool:
    return any("가" <= c <= "힣" for c in text)


def has_han(text: str) -> bool:
    return any("一" <= c <= "鿿" or "㐀" <= c <= "䶿" for c in text)


def distance(a: str, b: str) -> int:
    """編集距離（1文字の挿入・削除・置き換えを1と数える）。"""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def close(a: str, b: str) -> bool:
    """綴りが1文字違い（8文字以上なら2文字違い）まで。短い名前は近いとみなさない。"""
    if min(len(a), len(b)) < 4:
        return False
    return distance(a, b) <= (2 if min(len(a), len(b)) >= 8 else 1)


# ---------------------------------------------------------------- 韓国（ハングル）

CHO = ("g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h")
JUNG = ("a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we",
        "wi", "yu", "eu", "ui", "i")
JONG = ("", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p",
        "t", "t", "ng", "t", "t", "k", "t", "p", "t")
# 母音・子音の書き方のゆれをならす。上から順に置き換える（weo を eo より先に、など）
KO_FOLD = (("weo", "wo"), ("woo", "u"), ("wu", "u"), ("eo", "u"), ("ou", "u"), ("oo", "u"),
           ("eu", "u"), ("ee", "i"), ("ae", "e"), ("ai", "e"), ("oi", "oe"), ("wh", "w"),
           ("ch", "c"), ("j", "c"), ("sh", "s"), ("g", "k"), ("d", "t"), ("b", "p"), ("r", "l"))
# 姓は決まった書き方が多いので、表で持つ（表にない姓は1音ずつのローマ字で比べる）
KO_SURNAME = {
    "김": ("kim", "gim"), "이": ("lee", "yi", "rhee", "i", "ri", "rhie"), "박": ("park", "pak", "bak"),
    "최": ("choi", "choe", "chey", "choy"), "정": ("jeong", "jung", "chung", "joung", "cheong", "jong"),
    "강": ("kang", "gang"), "조": ("cho", "jo", "joe"), "윤": ("yoon", "yun", "youn"),
    "장": ("jang", "chang"), "임": ("lim", "im", "yim", "rim"), "한": ("han",), "오": ("oh", "o"),
    "서": ("seo", "suh", "so"), "신": ("shin", "sin"), "권": ("kwon", "gwon", "kweon"),
    "황": ("hwang",), "안": ("ahn", "an"), "송": ("song",), "류": ("ryu", "ryoo", "yoo", "yu", "lyu", "rew"),
    "유": ("yoo", "yu", "you", "ryu"), "전": ("jeon", "jun", "chun", "chon"), "홍": ("hong",),
    "고": ("ko", "go", "koh"), "문": ("moon", "mun"), "양": ("yang", "ryang"), "손": ("son", "sohn"),
    "배": ("bae", "pae", "bai"), "백": ("baek", "paek", "back", "baik", "paik"),
    "허": ("heo", "huh", "hur", "her"), "남": ("nam",), "심": ("shim", "sim"), "노": ("noh", "roh", "no", "ro"),
    "하": ("ha",), "곽": ("kwak", "gwak"), "성": ("sung", "seong"), "차": ("cha",),
    "주": ("joo", "ju", "chu", "choo"), "우": ("woo", "u", "wu"), "구": ("koo", "ku", "gu"),
    "민": ("min",), "진": ("jin", "chin"), "나": ("na", "ra"), "지": ("ji", "chi", "jee"),
    "엄": ("eom", "um", "uhm"), "원": ("won", "weon"), "천": ("cheon", "chun"), "방": ("bang", "pang"),
    "공": ("kong", "gong"), "현": ("hyun", "hyeon"), "함": ("ham",), "변": ("byun", "byeon", "pyun"),
    "염": ("yeom", "yum", "youm"), "여": ("yeo", "yuh", "yoh"), "추": ("chu", "choo"), "도": ("do", "doh"),
    "석": ("seok", "suk", "sok"), "선": ("sun", "seon"), "설": ("seol", "sul"), "길": ("gil", "kil"),
    "연": ("yeon", "yun", "youn"), "위": ("wi", "wee"), "표": ("pyo",), "명": ("myung", "myeong"),
    "기": ("ki", "gi"), "왕": ("wang",), "금": ("keum", "geum", "kum"), "육": ("yuk", "yook"),
    "인": ("in",), "어": ("eo", "uh", "oh"), "은": ("eun",), "편": ("pyun", "pyeon"), "용": ("yong",),
    "경": ("kyung", "gyeong", "kyeong"), "남궁": ("namgoong", "namkung", "namgung"),
    "황보": ("hwangbo",), "제갈": ("jegal",), "선우": ("sunwoo", "seonu", "seonwoo"),
    "독고": ("dokgo", "tokko"), "사공": ("sagong",),
}


def hangul_roman(text: str) -> str:
    """ハングルを1音ずつ文化観光部式のローマ字にする。音のつながりによる変化は付けない（旅券と同じ）。"""
    out = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append(CHO[code // 588] + JUNG[(code % 588) // 28] + JONG[code % 28])
        elif ch.isalpha():
            out.append(letters(ch))
    return "".join(out)


def ko_fold(text: str) -> str:
    folded = letters(text)
    for old, new in KO_FOLD:
        folded = folded.replace(old, new)
    return re.sub(r"(.)\1+", r"\1", folded)


def split_korean(name: str) -> tuple[str, str]:
    name = "".join(name.split())
    if len(name) >= 3 and name[:2] in KO_SURNAME:
        return name[:2], name[2:]
    return name[:1], name[1:]


def korean_surname_ok(surname: str, last: str) -> bool:
    spelled = letters(last)
    choices = KO_SURNAME.get(surname, ()) + (hangul_roman(surname),)
    return spelled in choices or ko_fold(spelled) in {ko_fold(c) for c in choices}


def korean_name(native: str, last: str, first: str) -> tuple[str, str]:
    """(「一致」「近い」「」, 説明)。"""
    surname, given = split_korean(native)
    roman = hangul_roman(given)
    want, got = ko_fold(roman), ko_fold(first)
    surname_ok = korean_surname_ok(surname, last)
    said = f"ハングルの読み（{hangul_roman(surname)} {roman}）"
    if surname_ok and want == got:
        return FULL, f"{said}が {last} {first} と一致"
    if surname_ok and close(want, got):
        return NEAR, f"{said}と姓は一致、名が近い（{first}）"
    if not surname_ok and want == got:
        return NEAR, f"{said}と名は一致、姓が違う（{last}）"
    return "", ""


# ---------------------------------------------------------------- 台湾（漢字）

PY_INITIALS = ("zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x",
               "r", "z", "c", "s", "y", "w")
WG_INITIAL = {"b": "p", "d": "t", "g": "k", "zh": "ch", "j": "ch", "q": "ch", "x": "hs", "r": "j",
              "z": "ts", "c": "ts"}
WG_FINAL = {"ong": "ung", "iong": "iung", "ian": "ien", "ie": "ieh", "ve": "ueh", "van": "uan",
            "vn": "un", "v": "u", "er": "erh"}
WG_Y = {"i": "i", "ou": "yu", "an": "yen", "e": "yeh", "ong": "yung", "v": "yu", "ve": "yueh",
        "van": "yuan", "vn": "yun"}
# 名前で読みの変わる字。macOS の変換は1つしか返さないので、ここにある字は両方試す
HAN_EXTRA = {
    "曾": ("zeng", "ceng"), "柏": ("bai", "bo"), "單": ("shan", "dan"), "解": ("xie", "jie"),
    "樂": ("le", "yue"), "長": ("chang", "zhang"), "重": ("zhong", "chong"), "行": ("xing", "hang"),
    "朝": ("chao", "zhao"), "傳": ("chuan", "zhuan"), "區": ("ou", "qu"), "仇": ("qiu", "chou"),
    "查": ("zha", "cha"), "翟": ("zhai", "di"), "沈": ("shen", "chen"), "繆": ("miao", "mou"),
    "蓋": ("gai", "ge"), "員": ("yuan", "yun"), "晟": ("sheng", "cheng"), "莘": ("shen", "xin"),
    "茜": ("qian", "xi"), "薄": ("bo", "bao"), "尉": ("wei", "yu"), "覃": ("qin", "tan"),
}
# 台湾の旅券でよく見る、決まりから外れた姓の書き方
HAN_SURNAME = {
    "李": ("lee",), "黃": ("hwang", "wong"), "陳": ("chan", "tan"), "張": ("cheung",),
    "吳": ("woo", "ng"), "林": ("lim", "lam"), "王": ("ong",), "蔡": ("tsay", "choi"), "周": ("chow",),
    "葉": ("yip",), "劉": ("lau",), "楊": ("young",), "郭": ("kwok",), "胡": ("hoo",), "余": ("yee",),
    "游": ("yo",), "盧": ("lo",), "何": ("hoh",),
}
HAN_COMPOUND = ("歐陽", "張簡", "司馬", "諸葛", "范姜", "上官", "東方", "司徒")
TONED_V = str.maketrans({"ǖ": "v", "ǘ": "v", "ǚ": "v", "ǜ": "v", "ü": "v"})
MANDARIN_JS = ('ObjC.import("Foundation");function run(argv){var o={};JSON.parse(argv[0]).forEach('
               'function(c){o[c]=$(c).stringByApplyingTransformReverse($.NSStringTransformMandarinToLatin,'
               'false).js});return JSON.stringify(o)}')


def mandarin(chars) -> dict[str, str]:
    """漢字1字ずつの中国語の読み（声調なしの拼音、ü は v）。macOS の変換を使い、使えなければ空。"""
    chars = sorted({c for c in chars if has_han(c)})
    if not chars:
        return {}
    try:
        done = subprocess.run(["osascript", "-l", "JavaScript", "-e", MANDARIN_JS,
                               json.dumps(chars, ensure_ascii=False)],
                              capture_output=True, text=True, timeout=60, check=True)
        raw = json.loads(done.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}
    return {c: re.sub(r"[^a-z]", "", plain(str(r).translate(TONED_V))) for c, r in raw.items()}


def split_pinyin(syllable: str) -> tuple[str, str]:
    initial = next((i for i in PY_INITIALS if syllable.startswith(i)), "")
    return initial, syllable[len(initial):]


def wade_giles(syllable: str) -> str:
    """拼音1音（声調なし、ü は v）を、旅券で使うウェード式（アポストロフィなし）にする。"""
    initial, final = split_pinyin(syllable)
    if initial in ("j", "q", "x", "y") and final.startswith("u"):
        final = "v" + final[1:]  # j・q・x・y のあとの u は ü
    if initial == "y":
        return WG_Y.get(final, "y" + final)
    if initial == "w":
        return syllable
    if final == "i" and initial in ("zh", "ch", "sh", "r"):
        return WG_INITIAL.get(initial, initial) + "ih"
    if final == "i" and initial in ("z", "c", "s"):
        return "ssu" if initial == "s" else "tzu"
    head = WG_INITIAL.get(initial, initial)
    if final == "e":
        final = "o" if initial in ("g", "k", "h", "") else "e"
    elif final == "uo":
        final = "uo" if initial in ("g", "k", "h", "sh") else "o"
    else:
        final = WG_FINAL.get(final, final)
    return head + final


def tongyong(syllable: str) -> str:
    """拼音1音を通用拼音に寄せる（台湾の旅券で見る jh・si・uei・wun・fong など）。"""
    initial, final = split_pinyin(syllable)
    if initial in ("j", "q", "x") and final.startswith("u"):
        final = "yu" + final[1:]
    head = {"zh": "jh", "q": "c", "x": "s"}.get(initial, initial)
    if final == "i" and initial in ("zh", "ch", "sh", "r", "z", "c", "s"):
        final = "ih"
    elif final == "eng" and initial in ("b", "p", "m", "f", "w"):
        final = "ong"
    elif initial == "w" and final == "en":
        final = "un"
    else:
        final = {"iu": "iou", "ui": "uei", "v": "yu", "ve": "yue"}.get(final, final)
    return head + final


def han_spellings(char: str, readings: dict[str, str]) -> set[str]:
    """漢字1字のローマ字の書き方の候補（漢語拼音・ウェード式・通用拼音と、そのゆれ）。"""
    out: set[str] = set()
    for syllable in {readings.get(char, ""), *HAN_EXTRA.get(char, ())} - {""}:
        forms = {syllable.replace("v", "u"), wade_giles(syllable), tongyong(syllable)}
        if "v" in syllable:
            forms |= {syllable.replace("v", "yu"), syllable}
        if syllable in ("zi", "ci"):
            forms |= {"tsu", "tzu"}
        if syllable == "si":
            forms |= {"szu", "ssu", "sih"}
        for form in list(forms):
            if form.endswith("ung"):
                forms.add(form[:-3] + "ong")
            if form.endswith("ui"):
                forms.add(form[:-2] + "uei")
        out |= forms
    return out


def split_han(name: str) -> tuple[str, str]:
    name = "".join(name.split())
    if len(name) >= 3 and name[:2] in HAN_COMPOUND:
        return name[:2], name[2:]
    return name[:1], name[1:]


def joined(parts: list[set[str]]) -> set[str]:
    out = {""}
    for options in parts:
        out = {head + tail for head in out for tail in options}
    return out


def han_name(native: str, last: str, first: str, readings: dict[str, str]) -> tuple[str, str]:
    surname, given = split_han(native)
    if not all(readings.get(c) or c in HAN_EXTRA for c in surname + given):
        return "", ""  # 読みが取れない（macOS の変換が使えない）
    surnames = joined([han_spellings(c, readings) for c in surname])
    surnames |= set(HAN_SURNAME.get(surname, ()))
    givens = joined([han_spellings(c, readings) for c in given])
    spelled_last, spelled_first = letters(last), letters(first)
    reading = " ".join(readings.get(c) or HAN_EXTRA[c][0] for c in surname + given).replace("v", "ü")
    said = f"漢字の読み（{reading}）"
    if spelled_last in surnames and spelled_first in givens:
        return FULL, f"{said}が {last} {first} と一致"
    if spelled_last in surnames and any(close(g, spelled_first) for g in givens):
        return NEAR, f"{said}と姓は一致、名が近い（{first}）"
    if spelled_last not in surnames and spelled_first in givens:
        return NEAR, f"{said}と名は一致、姓が違う（{last}）"
    return "", ""


# ---------------------------------------------------------------- ほか（スペイン語などの綴り）

LATIN_FOLD = ((r"ph", "f"), (r"qu", "k"), (r"c(?=[eiy])", "s"), (r"c", "k"), (r"z", "s"), (r"v", "b"),
              (r"ll", "y"), (r"(?<![cs])h", ""), (r"y(?![aeiou])", "i"), (r"(.)\1+", r"\1"))
PARTICLES = {"de", "del", "la", "las", "los", "da", "dos", "van", "der", "den", "von", "y"}


def latin_fold(word: str) -> str:
    for pattern, repl in LATIN_FOLD:
        word = re.sub(pattern, repl, word)
    return word


def latin_words(text) -> list[str]:
    return [latin_fold(w) for w in re.sub(r"[^a-z]+", " ", plain(text)).split() if w not in PARTICLES]


def prefix_either(a: list[str], b: list[str]) -> bool:
    """どちらかが、もう一方の頭の部分と同じ（2つ目の姓が片方にしかない、など）。"""
    n = min(len(a), len(b))
    return n > 0 and a[:n] == b[:n]


def in_order(part: list[str], whole: list[str]) -> bool:
    """part の語が、whole の中に同じ順で全部ある。"""
    rest = iter(whole)
    return bool(part) and all(any(w == p for w in rest) for p in part)


def latin_name(name: str, last: str, first: str) -> tuple[str, str]:
    """名と第1姓で比べる。名簿の名前は「名… 姓…」の順（「姓, 名」の形も読む）。"""
    surnames, givens = latin_words(last), latin_words(first)
    if "," in name:
        family, given = name.split(",", 1)
        splits = [(latin_words(given), latin_words(family))]
    else:
        words = latin_words(name)
        splits = [(words[:k], words[k:]) for k in range(1, len(words))]
    best = ("", "")
    for want_given, want_family in splits:
        family_ok = prefix_either(want_family, surnames) or "".join(want_family) == "".join(surnames)
        given_ok = in_order(want_given, givens)
        if family_ok and given_ok:
            return FULL, f"名と姓が {last}, {first} と一致（綴りのゆれをならして比べた）"
        if family_ok and want_given and any(close(want_given[0], g) for g in givens):
            best = (NEAR, f"姓は一致、名の綴りが近い（{first}）")
        elif (given_ok and want_family and surnames and close(want_family[0], surnames[0])
              and not best[0]):
            best = (NEAR, f"名は一致、姓の綴りが近い（{last}）")
    return best


# ---------------------------------------------------------------- 名前以外の項目

POS_GROUP = {"P": {"P"}, "C": {"C"}, "IF": {"IF"}, "INF": {"IF"}, "1B": {"IF"}, "2B": {"IF"},
             "3B": {"IF"}, "SS": {"IF"}, "OF": {"OF"}, "LF": {"OF"}, "CF": {"OF"}, "RF": {"OF"},
             "UTL": {"C", "IF", "OF"}, "UT": {"C", "IF", "OF"}, "DH": {"C", "IF", "OF"}}
POS_JA = {"P": "投手", "C": "捕手", "IF": "内野手", "OF": "外野手"}
HAND_JA = {"R": "右", "L": "左", "S": "両"}


def positions(text) -> set[str]:
    out: set[str] = set()
    for part in re.split(r"[/,\s]+", str(text or "").upper()):
        out |= POS_GROUP.get(part, set())
    return out


def year_of(text) -> str:
    found = re.search(r"(19|20)\d\d", str(text or ""))
    return found.group(0) if found else ""


def fields(announced: dict, registered: dict) -> tuple[list[str], list[str]]:
    """(合う項目, 食い違う項目)。片方にしか書いていない項目は数えない。"""
    agree, clash = [], []
    mine, theirs = positions(announced.get("position")), positions(registered.get("position"))
    if mine and theirs:
        if mine & theirs:
            agree.append("・".join(POS_JA[p] for p in sorted(mine & theirs)) + "同士"
                         if len(mine & theirs) == 1 else "守備の区分")
        else:
            clash.append(f"守備（名簿 {announced.get('position')}、登録 {registered.get('position')}）")
    for key, label in (("throws", "投"), ("bats", "打")):
        a = str(announced.get(key) or "").strip().upper()[:1]
        r = str(registered.get(key) or "").strip().upper()[:1]
        if a and r:
            if a == r:
                agree.append(f"{HAND_JA.get(a, a)}{label}")
            else:
                clash.append(f"{label}（名簿 {HAND_JA.get(a, a)}、登録 {HAND_JA.get(r, r)}）")
    a, r = year_of(announced.get("birth")), year_of(registered.get("yob"))
    if a and r:
        (agree if a == r else clash).append(f"{a}年生" if a == r else f"生年（名簿 {a}、登録 {r}）")
    a, r = str(announced.get("number") or "").strip(), str(registered.get("uniform") or "").strip()
    if a and r:
        (agree if a == r else clash).append(f"背番号{a}" if a == r else f"背番号（名簿 {a}、登録 {r}）")
    return agree, clash


# ---------------------------------------------------------------- 照合


def wbsc_name(row: dict) -> str:
    return br.name_of(row)


def same_words(a, b) -> bool:
    return sorted(re.sub(r"[^a-z]+", " ", plain(a)).split()) == sorted(re.sub(r"[^a-z]+", " ", plain(b)).split())


def name_match(announced: dict, registered: dict, readings: dict, past: list[dict]) -> tuple[str, str]:
    """名簿の1人と登録の1人の名前を比べる。past は名簿照合.csv でこの名簿の選手に結んだ行。"""
    native = str(announced.get("name") or "")
    last, first = registered.get("lastname") or "", registered.get("firstname") or ""
    for row in past:  # 過去の大会と同じ登録名・生年なら、読みを比べなくても同じ人
        if same_words(row.get("wbsc_name"), wbsc_name(registered)) and \
                year_of(row.get("birth")) == year_of(registered.get("yob")):
            return FULL, f"名簿照合.csv で結んだ過去の記録と登録名・生年が同じ（{row.get('wbsc_name')}）"
    if has_hangul(native):
        return korean_name(native, last, first)
    if has_han(native):
        return han_name(native, last, first, readings)
    return latin_name(native, last, first)


def match_team(announced: list[dict], registered: list[dict], readings: dict,
               links: dict[str, list[dict]]) -> dict:
    """1チーム分。confirmed（確認済みの組）、review（要確認の候補）、名簿だけ・登録だけを返す。"""
    pairs = []
    for i, a in enumerate(announced):
        for j, r in enumerate(registered):
            level, said = name_match(a, r, readings, links.get(a.get("name") or "", []))
            if level:
                agree, clash = fields(a, r)
                pairs.append({"i": i, "j": j, "level": level, "said": said, "agree": agree, "clash": clash})
    full_i = Counter(p["i"] for p in pairs if p["level"] == FULL)
    full_j = Counter(p["j"] for p in pairs if p["level"] == FULL)
    confirmed = [p for p in pairs if p["level"] == FULL and not p["clash"]
                 and full_i[p["i"]] == 1 and full_j[p["j"]] == 1]
    done_i, done_j = {p["i"] for p in confirmed}, {p["j"] for p in confirmed}
    review = [p for p in pairs if p["i"] not in done_i and p["j"] not in done_j]
    for p in review:
        reasons = []
        if p["level"] == NEAR:
            reasons.append("名前が近いだけ")
        if full_i[p["i"]] > 1:
            reasons.append("名簿の1人に一致する登録が2人以上")
        if full_j[p["j"]] > 1:
            reasons.append("登録の1人に一致する名簿が2人以上")
        if p["clash"]:
            reasons.append("食い違い: " + "、".join(p["clash"]))
        p["why"] = "／".join(reasons)
    # 結べる相手がいない選手。名前の近い相手が、もう別の選手と結ばれているだけのこともある
    seen_i, seen_j = {p["i"] for p in review}, {p["j"] for p in review}
    near_j: dict[int, list[str]] = {}
    for p in pairs:
        if p["i"] in done_i and p["j"] not in done_j:
            near_j.setdefault(p["j"], []).append(announced[p["i"]].get("name") or "")
    near_i: dict[int, list[str]] = {}
    for p in pairs:
        if p["j"] in done_j and p["i"] not in done_i:
            near_i.setdefault(p["i"], []).append(wbsc_name(registered[p["j"]]))
    return {
        "confirmed": confirmed,
        "review": review,
        "roster_only": [(i, near_i.get(i, [])) for i in range(len(announced))
                        if i not in done_i and i not in seen_i],
        "registered_only": [(j, near_j.get(j, [])) for j in range(len(registered))
                            if j not in done_j and j not in seen_j],
        "unsure_i": sorted(seen_i),
    }


def evidence(event: str, registered: dict, pair: dict) -> str:
    fetched = str(registered.get("fetched") or "")[:10]
    head = f"{event}のWBSC登録名簿（{fetched}取得、背番号{registered.get('uniform') or '?'}）" if fetched \
        else f"{event}のWBSC登録名簿（背番号{registered.get('uniform') or '?'}）"
    parts = [head, pair["said"]]
    if pair["agree"]:
        parts.append("・".join(pair["agree"]) + "が合う")
    parts.append("roster_match.py の案を差分で確かめて追加")
    return "。".join(parts)


def records(event: str) -> set[str]:
    """その大会の打撃・投球の記録に出てくる playerid。"""
    folder = br.DATA_ROOT / event
    return {str(row.get("playerid") or "") for name in ("batting.csv", "pitching.csv")
            for row in br.read_csv(folder / name)} - {""}


def plan(event: str, announced_rows: list[dict], roster_rows: list[dict], match_rows: list[dict],
         same_rows: list[dict]) -> dict:
    """全チームの案。名簿照合.csv に足す行、同一人物.csv に足す行、要確認の一覧、チームごとの数。"""
    teams_a = {r.get("team") for r in announced_rows} - {"", None}
    teams_r = {r.get("ioc") for r in roster_rows} - {"", None}
    linked = {(r.get("team"), str(r.get("playerid") or "")) for r in match_rows}
    by_pid = {(r.get("team"), str(r.get("playerid") or "")): r.get("roster_name") for r in match_rows}
    merged = {(str(r.get("keep_playerid") or ""), str(r.get("merge_playerid") or "")) for r in same_rows}
    played = records(event)
    readings = mandarin("".join(r.get("name") or "" for r in announced_rows
                                if r.get("team") in teams_r))
    out = {"add": [], "same": [], "later": [], "review": [], "counts": [],
           "no_roster": sorted(teams_r - teams_a), "no_registered": sorted(teams_a - teams_r),
           "readings_missing": bool([r for r in announced_rows if r.get("team") in teams_r
                                     and has_han(r.get("name") or "")]) and not readings}
    for team in sorted(teams_a & teams_r):
        announced = [r for r in announced_rows if r.get("team") == team]
        registered = [r for r in roster_rows if r.get("ioc") == team and r.get("playerid")]
        links: dict[str, list[dict]] = {}
        for row in match_rows:
            if row.get("team") == team:
                links.setdefault(row.get("roster_name") or "", []).append(row)
        result = match_team(announced, registered, readings, links)
        count = {"team": team, "announced": len(announced), "registered": len(registered),
                 "confirmed": len(result["confirmed"]), "unsure": len(result["unsure_i"]),
                 "roster_only": len(result["roster_only"]), "registered_only": len(result["registered_only"]),
                 "new": 0, "already": 0}
        for pair in result["confirmed"]:
            a, r = announced[pair["i"]], registered[pair["j"]]
            pid = str(r["playerid"])
            if (team, pid) in linked:
                if by_pid.get((team, pid)) != a.get("name"):  # 登録の選手が、別の名簿の選手と結ばれている
                    out["review"].append(review_row(team, a, r, pair, "名簿照合.csv で別の名簿の選手"
                                                    f"（{by_pid.get((team, pid))}）と結ばれている"))
                else:
                    count["already"] += 1
                continue
            count["new"] += 1
            out["add"].append({"team": team, "roster_name": a.get("name"), "playerid": pid,
                               "wbsc_name": wbsc_name(r), "birth": year_of(r.get("yob")),
                               "match": "確認済み", "evidence": evidence(event, r, pair)})
            if "離脱" in (a.get("status") or ""):
                out["review"].append(review_row(team, a, r, pair, "離脱の報道がある選手が登録されている"
                                                "（名簿の状態を見直す）"))
            for old in links.get(a.get("name") or "", []):
                old_pid = str(old.get("playerid") or "")
                if sl.person_key(old.get("wbsc_name") or "", year_of(old.get("birth")), team) == \
                        sl.person_key(wbsc_name(r), year_of(r.get("yob")), team) or (pid, old_pid) in merged:
                    continue
                same = {"team": team, "keep_playerid": pid, "merge_playerid": old_pid,
                        "evidence": f"今大会の登録名簿の {wbsc_name(r)}（{pid}）と、名簿照合.csv で"
                                    f"{a.get('name')}に結んでいた {old.get('wbsc_name')}（{old_pid}）。"
                                    "登録名か生年が違い、名前と生年の鍵では1人にまとまらないため"}
                (out["same"] if pid in played else out["later"]).append(same)
        for p in result["review"]:
            out["review"].append(review_row(team, announced[p["i"]], registered[p["j"]], p, p["why"]))
        for i, near in result["roster_only"]:
            out["review"].append(review_row(team, announced[i], None, None, "名簿にいて、結べる登録の選手がいない"
                                            + (f"（名前の近い {'・'.join(near)} は別の選手と結んだ）" if near else "")))
        for j, near in result["registered_only"]:
            out["review"].append(review_row(team, None, registered[j], None, "登録にいて、結べる名簿の選手がいない"
                                            + (f"（名前の近い {'・'.join(near)} は別の選手と結んだ）" if near else "")))
        out["counts"].append(count)
    return out


def review_row(team: str, announced: dict | None, registered: dict | None, pair: dict | None,
               why: str) -> dict:
    a, r = announced or {}, registered or {}
    return {
        "team": team,
        "roster_name": a.get("name") or "",
        "roster_position": a.get("position") or "",
        "roster_status": a.get("status") or "",
        "playerid": r.get("playerid") or "",
        "wbsc_name": wbsc_name(r) if r else "",
        "uniform": r.get("uniform") or "",
        "wbsc_position": r.get("position") or "",
        "bats_throws": f"{r.get('bats') or '?'}/{r.get('throws') or '?'}" if r else "",
        "yob": r.get("yob") or "",
        "name_match": (pair or {}).get("level", ""),
        "name_note": (pair or {}).get("said", ""),
        "agree": "・".join((pair or {}).get("agree", [])),
        "why": why,
    }


# ---------------------------------------------------------------- 書き出し


def csv_line(row: dict, columns: list[str]) -> str:
    buffer = StringIO()
    csv.writer(buffer, lineterminator="").writerow([row.get(c, "") for c in columns])
    return buffer.getvalue()


def append_rows(path: Path, rows: list[dict], columns: list[str]) -> None:
    """CSV の末尾に行を足す。改行の形（CRLF か LF か）は今のファイルに合わせる。"""
    if not rows:
        return
    existed = path.exists() and path.stat().st_size > 0
    data = path.read_bytes() if existed else b""
    newline = "\r\n" if b"\r\n" in data else "\n"
    with path.open("a", encoding="utf-8" if existed else "utf-8-sig", newline="") as handle:
        if existed and not data.endswith(b"\n"):
            handle.write(newline)
        writer = csv.writer(handle, lineterminator=newline)
        if not existed:
            writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(c, "") for c in columns])


def report(result: dict, args) -> None:
    print(f"\n{args.event} の登録名簿と名簿の照合")
    print(f"  名簿: {args.announced}\n  登録: {args.rosters}\n  照合表: {args.match}")
    if result["readings_missing"]:
        print("  注意: 漢字の読みが取れませんでした（macOS の変換が使えない）。台湾の選手は"
              "過去の照合と同じ登録名の人だけが結べます")
    print("\n  チーム  名簿 登録  確認済み（新しく足す/もうある） 要確認 名簿だけ 登録だけ")
    for c in result["counts"]:
        print(f"  {c['team']:6} {c['announced']:4} {c['registered']:4}  {c['confirmed']:4}"
              f"（{c['new']}/{c['already']}）{'':18}{c['unsure']:4} {c['roster_only']:7} {c['registered_only']:7}")
    if result["no_roster"]:
        print(f"  名簿がなく照合しないチーム: {', '.join(result['no_roster'])}")
    if result["no_registered"]:
        print(f"  登録名簿がまだないチーム: {', '.join(result['no_registered'])}")
    print(f"\n  名簿照合.csv に足す行（{len(result['add'])}行）")
    for row in result["add"]:
        print("  + " + csv_line(row, MATCH_FIELDS))
    if result["same"]:
        print(f"\n  同一人物.csv に足す行（{len(result['same'])}行）")
        for row in result["same"]:
            print("  + " + csv_line(row, SAME_FIELDS))
    if result["later"]:
        print(f"\n  今大会の記録が出てから同一人物.csv に足す組（{len(result['later'])}組。"
              "記録が出たあとに流し直すと上に出ます）")
        for row in result["later"]:
            print(f"    {row['team']} {row['keep_playerid']} ← {row['merge_playerid']}")
    unsure = [r for r in result["review"] if r["playerid"] and r["roster_name"]]
    alone = [r for r in result["review"] if not (r["playerid"] and r["roster_name"])]
    print(f"\n  要確認（人が見る。自動では結ばない）: 候補の組 {len(unsure)}・片方だけ {len(alone)}")
    for r in unsure:
        pos = f"（{r['roster_position']}）" if r["roster_position"] else ""
        detail = " ".join(x for x in (f"#{r['uniform']}" if r["uniform"] else "", r["wbsc_position"],
                                      r["bats_throws"], r["yob"]) if x)
        print(f"    {r['team']} {r['roster_name']}{pos}? {r['wbsc_name']} {detail} — {r['why']}")
    for r in alone:
        who = (f"{r['roster_name']}（{r['roster_position']}）" if r["roster_name"]
               else f"{r['wbsc_name']} #{r['uniform']} {r['wbsc_position']} {r['yob']}")
        print(f"    {r['team']} {who} — {r['why']}")


REVIEW_FIELDS = ["team", "roster_name", "roster_position", "roster_status", "playerid", "wbsc_name",
                 "uniform", "wbsc_position", "bats_throws", "yob", "name_match", "name_note", "agree", "why"]


def write_outputs(result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print()
    for name, rows, columns in (("名簿照合_案.csv", result["add"], MATCH_FIELDS),
                                ("名簿照合_要確認.csv", result["review"], REVIEW_FIELDS),
                                ("同一人物_案.csv", result["same"], SAME_FIELDS)):
        collect.write_csv(out_dir / name, [{c: row.get(c, "") for c in columns} for row in rows])
    print(f"  出力先 {out_dir}")


# ---------------------------------------------------------------- 決まりの確かめ


def selftest() -> int:
    ok, ng = 0, []

    def check(passed: bool, text: str) -> None:
        nonlocal ok
        if passed:
            ok += 1
        else:
            ng.append(text)

    check(hangul_roman("김도빈") == "gimdobin", "ハングルのローマ字 김도빈")
    for native, last, first, want in (
            ("최현석", "CHOI", "Hyunseok", FULL), ("임상우", "LIM", "Sangwoo", FULL),
            ("류현준", "RYU", "Hyeonjun", FULL), ("정안석", "JEONG", "Anseok", FULL),
            ("송재영", "SONG", "Jaeyoung", FULL), ("김도빈", "KIM", "Dobeen", FULL),
            ("이정현", "LEE", "Junghyun", FULL), ("김동현", "KIM", "Doohyun", ""),
            ("김두현", "KIM", "Donghyun", ""), ("박지호", "PARK", "Jiho", FULL)):
        got = korean_name(native, last, first)[0]
        check(got == want, f"韓国 {native} と {last} {first}: {got or '不一致'}（期待は {want or '不一致'}）")
    for py, want in (("guan", "kuan"), ("zi", "tzu"), ("xiang", "hsiang"), ("zhong", "chung"),
                     ("he", "ho"), ("jie", "chieh"), ("nian", "nien"), ("qiu", "chiu"), ("xin", "hsin"),
                     ("jun", "chun"), ("lv", "lu"), ("guo", "kuo"), ("luo", "lo"), ("yan", "yen"),
                     ("zhi", "chih"), ("xue", "hsueh"), ("rong", "jung"), ("cai", "tsai")):
        check(wade_giles(py) == want, f"ウェード式 {py} → {wade_giles(py)}（期待は {want}）")
    readings = {"曾": "ceng", "家": "jia", "輝": "hui", "尹": "yin", "柏": "bai", "淮": "huai",
                "陳": "chen", "品": "pin", "宏": "hong", "邱": "qiu", "鑫": "xin", "冠": "guan", "維": "wei"}
    for native, last, first, want in (
            ("曾家輝", "ZENG", "Jia-Huei", FULL), ("尹柏淮", "YIN", "Po-Huai", FULL),
            ("陳品宏", "CHEN", "Pin-Hong", FULL), ("邱鑫", "CHIU", "Hsin", FULL),
            ("邱冠維", "CHIU", "Hsin", "")):
        got = han_name(native, last, first, readings)[0]
        check(got == want, f"台湾 {native} と {last} {first}: {got or '不一致'}（期待は {want or '不一致'}）")
    for name, last, first, want in (
            ("Yeremi Lezcano", "LEZCANO RIOS", "Yeremy", FULL),
            ("Riquelme Odelín", "ODELIN", "Rikelmi", NEAR),
            ("Randal Díaz", "DIAZ MORALES", "Randal Gabriel", FULL),
            ("José Ignacio Bermúdez", "BERMUDEZ GARCIA", "José Ignacio", FULL),
            ("Luis González", "GONZALEZ MORENO", "Alejandro Javier", ""),
            ("Aiden Mc Allister", "MCALLISTER", "Aiden", FULL),
            ("Stef Van Duivenbooden", "VAN DUIVENBOODEN", "Stef", FULL)):
        got = latin_name(name, last, first)[0]
        check(got == want, f"綴り {name} と {last}, {first}: {got or '不一致'}（期待は {want or '不一致'}）")
    agree, clash = fields({"position": "UTL"}, {"position": "P"})
    check(bool(clash), "守備 UTL と P は食い違い")
    agree, clash = fields({"position": "IF", "throws": "R", "birth": "2003-01-03"},
                          {"position": "3B", "throws": "R", "yob": "2003"})
    check(not clash and len(agree) == 3, f"守備 IF と 3B・右投・生年が合う: {agree} {clash}")
    # 案の組み立て（記録のない大会キーで流すので、同一人物の組は「記録が出てから」に回る）
    result = plan("selftest-none",
                  [{"team": "CUB", "name": "José Ignacio Bermúdez", "position": "P"},
                   {"team": "CUB", "name": "Luis Pérez", "position": "IF"}],
                  [{"ioc": "CUB", "playerid": "900001", "lastname": "BERMUDEZ", "firstname": "Jose Ignacio",
                    "position": "P", "yob": "2003"},
                   {"ioc": "CUB", "playerid": "900002", "lastname": "PEREZ", "firstname": "Luiz",
                    "position": "IF", "yob": "2004"},
                   {"ioc": "CUB", "playerid": "900003", "lastname": "PERES", "firstname": "Luis",
                    "position": "OF", "yob": "2004"}],
                  [{"team": "CUB", "roster_name": "José Ignacio Bermúdez", "playerid": "637076",
                    "wbsc_name": "BERMUDEZ GARCIA, José Ignacio", "birth": "2003"}], [])
    check([r["playerid"] for r in result["add"]] == ["900001"], f"足す行は Bermúdez だけ: {result['add']}")
    check([r["merge_playerid"] for r in result["later"]] == ["637076"],
          f"Bermúdez の過去の記録を同一人物に回す: {result['later']}")
    perez = [r for r in result["review"] if r["roster_name"] == "Luis Pérez"]
    check(len(perez) == 2 and all("2人以上" in r["why"] for r in perez),
          f"候補が2人の Luis Pérez は要確認: {perez}")
    print(f"決まりの確かめ: {ok}件合格、{len(ng)}件不合格")
    for text in ng:
        print(f"  不合格: {text}")
    return 1 if ng else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--event", default=CURRENT, help="大会キー（既定は今大会）")
    parser.add_argument("--announced", type=Path, default=INFO / "今大会_発表名簿.csv", help="名簿のCSV")
    parser.add_argument("--rosters", type=Path, help="登録名簿（既定は 05_収集データ/<大会>/rosters.csv）")
    parser.add_argument("--match", type=Path, default=SITE_INFO / "名簿照合.csv", help="名簿照合.csv")
    parser.add_argument("--same", type=Path, default=SITE_INFO / "同一人物.csv", help="同一人物.csv")
    parser.add_argument("--out", type=Path, help="案の書き出し先（既定は 05_収集データ/<大会>/）")
    parser.add_argument("--apply", action="store_true", help="案の行を名簿照合.csv と同一人物.csv に足す")
    parser.add_argument("--skip", default="", help="案から外す登録の playerid（カンマ区切り）。外した選手は要確認に回る")
    parser.add_argument("--selftest", action="store_true", help="名前の比べ方の決まりを確かめる")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    args.rosters = args.rosters or br.DATA_ROOT / args.event / "rosters.csv"
    out_dir = args.out or br.DATA_ROOT / args.event
    if not args.rosters.exists():
        print(f"登録名簿がありません（{args.rosters}）。先に collect.py --event {args.event} --rosters を"
              "流してください。WBSCが名簿をまだ出していなければ、そこで「まだ出ていません」と出ます。",
              file=sys.stderr)
        return 1
    result = plan(args.event, br.read_csv(args.announced), br.read_csv(args.rosters),
                  br.read_csv(args.match), br.read_csv(args.same))
    skip = {pid.strip() for pid in args.skip.split(",")} - {""}
    if skip:
        for row in result["add"]:
            if row["playerid"] in skip:
                entry = dict.fromkeys(REVIEW_FIELDS, "")
                entry.update(team=row["team"], roster_name=row["roster_name"], playerid=row["playerid"],
                             wbsc_name=row["wbsc_name"], yob=row["birth"], why="--skip で案から外した")
                result["review"].append(entry)
        result["add"] = [row for row in result["add"] if row["playerid"] not in skip]
        result["same"] = [row for row in result["same"] if row["keep_playerid"] not in skip]
    report(result, args)
    try:
        write_outputs(result, out_dir)
    except collect.Refused as error:
        print(f"  止めました: {error}", file=sys.stderr)
        return 1
    if not args.apply:
        if result["add"] or result["same"]:
            print("\n  まだ何も足していません。上の行でよければ --apply を付けて流し直してください。")
        return 0
    append_rows(args.match, result["add"], MATCH_FIELDS)
    append_rows(args.same, result["same"], SAME_FIELDS)
    print(f"\n  足しました: {args.match.name} に{len(result['add'])}行、{args.same.name} に{len(result['same'])}行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
