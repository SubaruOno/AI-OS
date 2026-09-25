#!/usr/bin/env python3
"""各社のマイページURLとログインIDをChromeの手元データから集めて台帳にする。

集めるのは、URL、タイトルから分かる会社名、そしてログインIDだけ。パスワードは
読まないし、保存もしない。ログインIDは Chrome の「保存したログイン情報」
（Login Data）の username_value 列だけを取り出す。password_value 列には触れない。

履歴もログイン情報も読み取り専用で扱う。Chrome が起動中でも読めるように一時
ファイルへコピーしてから開く。元のファイルには触らない。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR.parents[1]
PRIVATE = WORKSPACE / "private" / "job-hunt"
MYPAGES_PATH = PRIVATE / "mypages.json"
MANUAL_PATH = PRIVATE / "mypages-manual.json"

CHROME_ROOT = Path.home() / "Library/Application Support/Google/Chrome"

# 企業ごとのマイページを持つATS。ここに無いドメインは履歴から拾わない。
AXOL_ZW = re.compile(r"^/zw/s/([a-z0-9_]+)/")
AXOL_FF = re.compile(r"^/ff/c/([a-z0-9_]+)/")
I_WEBS_HOST = re.compile(r"^mypage\.\d+\.i-webs\.jp$")
I_WEB_JPN_HOST = re.compile(r"^mypage\.\d+\.i-web\.jpn\.com$")
SNAR_HOST = re.compile(r"^([a-z0-9-]+)\.snar\.jp$")
SAIYO_HOST = re.compile(r"^([a-z0-9-]+)\.saiyo\.jp$")

ATS_LABEL = {
    "axol": "axol",
    "axol-ff": "axol (job)",
    "i-webs": "i-webs",
    "i-web-jpn": "i-web",
    "snar": "snar",
    "saiyo": "saiyo",
    "mufg-bk": "三菱UFJ銀行",
    "smbc": "三井住友銀行",
    "nri": "NRI",
    "e2r": "eARTH",
    "sony": "ソニー",
    "talent-p": "talent-p",
}

# 履歴に出るが就活と関係ないもの。会社名の誤ラベルを避けるため弾く。
NOT_JOB_HOSTS = ("ex.accea.co.jp", "webupload.accea.co.jp", "www.openwork.jp")

# 会社名ではなく画面の名前。タイトルから会社名を選ぶときに避ける。
UI_WORDS = ("ログイン", "トップページ", "入力", "確認", "完了", "選択", "詳細",
            "メッセージ", "一覧", "エラー", "検索", "not found", "My Page")

# タイトルから落とす飾り。会社名だけを残すために右側から繰り返し外す。
TITLE_NOISE = re.compile(
    r"[\s　|｜]*(マイページ|Ｍｙ ?Page|My ?Page|マイ ?ページ|新卒採用|インターンシップ"
    r"|Recruiting MyPage|Recruiting|Personal Page|採用ページ|採用|ログイン"
    r"|新卒|ページ|20\d\d年?度?|28卒|向け)$"
)

# タイトルからは分からないが、会社名が確定しているものの正式名。
OFFICIAL_NAMES = {
    "axol:accenture_28": "アクセンチュア",
    "axol:hakuhodo_28": "博報堂",
    "axol:ibm_group_28": "日本IBM",
    "axol:kddi_28": "KDDI",
    "axol:marubeni_28": "丸紅",
    "axol:mri_28": "三菱総合研究所",
    "axol:muit_28": "三菱UFJインフォメーションテクノロジー",
    "axol:nissay_28": "日本生命保険",
    "axol:obc_28": "オービックビジネスコンサルタント",
    "axol:ridgelinez_28": "Ridgelinez",
    "axol:sei_28": "住友電気工業",
    "axol:skygroup_28": "Sky",
    "axol:sumitomocorp_28": "住友商事",
    "axol:dirg_28": "大和総研",
    "axol-ff:pwc": "PwCコンサルティング",
    "snar:cyberagent": "サイバーエージェント",
    "snar:docomo-recruit": "NTTドコモ",
    "snar:docomocs-recruit": "ドコモCS",
    "snar:lycorp": "LINEヤフー",
    "snar:moneyforward-recruit": "マネーフォワード",
    "snar:nttdata": "NTTデータグループ",
    "snar:nttdmse-recruit": "NTTデータMSE",
    "snar:sansan": "Sansan",
    "snar:softbank-recruit": "ソフトバンク",
    "snar:toyota-saiyo": "トヨタ自動車",
    "i-webs:abeam2028": "アビームコンサルティング",
    "i-webs:ctc2028": "伊藤忠テクノソリューションズ",
    "i-webs:gmo2028": "GMOインターネットグループ",
    "i-webs:murc2028": "三菱UFJリサーチ&コンサルティング",
    "i-webs:nft2028": "NTTデータ フィナンシャルテクノロジー",
    "i-webs:nssolgroup-2028": "NS Solutions",
    "i-webs:pwc_newgrads28": "PwCコンサルティング",
    "i-webs:rakuten-bu-2028": "楽天",
    "i-webs:sankeibldg2028": "サンケイビル",
    "i-webs:sigmaxyz28": "シグマクシス",
    "i-webs:simplex2028": "シンプレクス・ホールディングス",
    "i-webs:sojitz_group2028": "双日",
    "i-web-jpn:scsk2028": "SCSK",
    "mufg-bk:mufgbank2028": "三菱UFJ銀行",
    "smbc:2028": "三井住友銀行",
    "saiyo:orix-group": "オリックスグループ",
    "nri:2028": "野村総合研究所",
    "e2r:fr": "ファーストリテイリング",
    "sony:2028": "ソニーグループ",
    "talent-p:74249f95": "（会社名未特定）",
}


def ats_of(host: str, path: str):
    """ホストとパスから、マイページの置き場所を1つに決める。"""
    if host == "axol.jp":
        m = AXOL_ZW.match(path)
        if m:
            slug = m.group(1)
            base = f"https://axol.jp/zw/s/{slug}"
            return {"key": f"axol:{slug}", "ats": "axol",
                    "login_url": f"{base}/mypage/login", "home_url": f"{base}/mypage/top"}
        return None
    if host == "job.axol.jp":
        m = AXOL_FF.match(path)
        if m:
            slug = m.group(1)
            url = f"https://job.axol.jp/ff/c/{slug}/mypage/top"
            return {"key": f"axol-ff:{slug}", "ats": "axol-ff",
                    "login_url": url, "home_url": url}
        return None
    if I_WEBS_HOST.match(host) or I_WEB_JPN_HOST.match(host):
        slug = path.strip("/").split("/")[0]
        if slug:
            ats = "i-webs" if I_WEBS_HOST.match(host) else "i-web-jpn"
            base = f"https://{host}/{slug}/"
            return {"key": f"{ats}:{slug}", "ats": ats, "login_url": base, "home_url": base}
        return None
    m = SNAR_HOST.match(host)
    if m:
        slug = m.group(1)
        return {"key": f"snar:{slug}", "ats": "snar",
                "login_url": f"https://{host}/login.aspx", "home_url": f"https://{host}/"}
    if host == "working.nri.co.jp" and path.startswith("/mypage2028"):
        return {"key": "nri:2028", "ats": "nri",
                "login_url": "https://working.nri.co.jp/mypage2028/",
                "home_url": "https://working.nri.co.jp/mypage2028/"}
    if host == "www.e2r.jp" and "/fr_newgrad/" in path:
        return {"key": "e2r:fr", "ats": "e2r",
                "login_url": "https://www.e2r.jp/ja/fr_newgrad/gfs/logon.html",
                "home_url": "https://www.e2r.jp/ja/fr_newgrad/gfs/logon.html"}
    if host == "www.recruit.sony.co.jp" and path.startswith("/2028"):
        return {"key": "sony:2028", "ats": "sony",
                "login_url": "https://www.recruit.sony.co.jp/2028/",
                "home_url": "https://www.recruit.sony.co.jp/2028/"}
    if host == "recruit.talent-p.net":
        token = path.strip("/").split("/")[-1]
        if not token or token.lower() in ("login", "auth"):
            return None
        slug = token[:8]
        return {"key": f"talent-p:{slug}", "ats": "talent-p",
                "login_url": f"https://{host}/Auth/Login/{token}",
                "home_url": f"https://{host}/Auth/Login/{token}"}
    if host == "www.mypage.bk.mufg.jp":
        slug = path.strip("/").split("/")[0]
        if slug:
            base = f"https://{host}/{slug}/"
            return {"key": f"mufg-bk:{slug}", "ats": "mufg-bk", "login_url": base, "home_url": base}
        return None
    if host == "mypage.smbc-recruitment.jp":
        year = path.strip("/").split("/")[0]
        if year:
            base = f"https://{host}/{year}/"
            return {"key": f"smbc:{year}", "ats": "smbc", "login_url": base, "home_url": base}
        return None
    m = SAIYO_HOST.match(host)
    if m and m.group(1) != "www":
        slug = m.group(1)
        year = path.strip("/").split("/")[0]
        base = f"https://{host}/{year}/" if year else f"https://{host}/"
        return {"key": f"saiyo:{slug}", "ats": "saiyo", "login_url": base, "home_url": base}
    return None


def name_score(name: str) -> int:
    """会社名らしさの点数。画面の名前は低くする。"""
    if not name:
        return -1
    score = len(name)
    for word in UI_WORDS:
        if word in name:
            score -= 30
    return score


def strip_corp(name: str) -> str:
    """末尾の法人格だけを落とす。途中の「ホールディングス」は残す。"""
    changed = True
    while changed:
        changed = False
        for affix in ("株式会社", "（株）", "(株)", "合同会社"):
            if name.endswith(affix):
                name = name[: -len(affix)]
                changed = True
            elif name.startswith(affix):
                name = name[len(affix):]
                changed = True
    return name.strip(" 　|・-")


def clean_name(title: str) -> str:
    """タイトルから会社名だけを取り出す。"""
    name = unicodedata.normalize("NFKC", title or "")
    name = re.split(r"[|｜]", name)[0].strip()
    name = re.sub(r"^[【\[（(][^】\]）)]*[】\]）)]", "", name).strip()
    name = strip_corp(name)
    changed = True
    while changed and name:
        changed = False
        stripped = TITLE_NOISE.sub("", name).strip(" 　|｜・-")
        if stripped != name:
            name = stripped
            changed = bool(stripped)
    return strip_corp(name)


def chrome_history_candidates() -> list[Path]:
    if not CHROME_ROOT.exists():
        return []
    found = list(CHROME_ROOT.glob("*/History"))
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def chrome_login_databases() -> list[Path]:
    if not CHROME_ROOT.exists():
        return []
    return sorted(CHROME_ROOT.glob("*/Login Data"))


def _readonly_copy(path: Path):
    tmp = tempfile.TemporaryDirectory()
    copy = Path(tmp.name) / path.name
    shutil.copy2(path, copy)
    return tmp, copy


def read_rows(history: Path):
    """閲覧履歴から url/title/visit_count を読む。"""
    tmp, copy = _readonly_copy(history)
    try:
        conn = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        try:
            return conn.execute(
                "select url, title, visit_count from urls"
            ).fetchall()
        finally:
            conn.close()
    finally:
        tmp.cleanup()


def read_login_names(login_db: Path):
    """保存したログイン情報から origin と ユーザー名 だけを読む。

    password_value 列は select しない。パスワードは読まない。
    """
    tmp, copy = _readonly_copy(login_db)
    try:
        conn = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        try:
            return conn.execute("select origin_url, username_value from logins").fetchall()
        finally:
            conn.close()
    finally:
        tmp.cleanup()


def empty_site(found: dict) -> dict:
    return {
        "key": found["key"],
        "ats": found["ats"],
        "login_url": found["login_url"],
        "home_url": found["home_url"],
        "official_name": "",
        "names": {},
        "visits": 0,
        "last_seen": "",
    }


def candidates_from_history(histories) -> dict:
    """履歴からマイページのURLを1社1件に絞って取り出す。"""
    sites = {}
    for history in histories:
        for url, title, visits in read_rows(history):
            parts = urlsplit(url)
            if parts.netloc in NOT_JOB_HOSTS:
                continue
            found = ats_of(parts.netloc, parts.path)
            if not found:
                continue
            row = sites.setdefault(found["key"], empty_site(found))
            row["visits"] += visits or 0
            for name in (title or "").split("|"):
                name = name.strip()
                if name:
                    row["names"][name] = row["names"].get(name, 0) + 1
    for key, row in list(sites.items()):
        counts = row.pop("names", {})
        if counts:
            row["official_name"] = max(
                counts.items(), key=lambda kv: (kv[1], name_score(clean_name(kv[0])), len(kv[0]))
            )[0]
        if "not found" in (row["official_name"] or "").lower():
            del sites[key]
    return sites


EMAIL_ONLY = re.compile(r"^[a-z0-9.-]+\.(com|jp|net|org)$", re.I)


def normalize_login_id(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").replace("　", " ").strip()


def collect_login_ids(keys_hint: set[str]):
    """保存ログイン情報から、企業ごとのログインIDらしき値を選ぶ。

    password_value は読まない。会社をまたいで同じ値が出るときは、その企業に
    専用の値があればそちらを優先する（取り違え対策）。
    """
    by_key: dict[str, list[tuple[str, str]]] = {}
    seen_keys: dict[str, set[str]] = {}
    for db in chrome_login_databases():
        try:
            rows = read_login_names(db)
        except sqlite3.Error:
            continue
        for origin, user in rows:
            parts = urlsplit(origin or "")
            found = ats_of(parts.netloc, parts.path)
            if not found:
                continue
            value = normalize_login_id(user)
            if not value or EMAIL_ONLY.match(value):
                continue
            by_key.setdefault(found["key"], []).append((origin, value))
            seen_keys.setdefault(value, set()).add(found["key"])

    picked = {}
    for key, candidates in by_key.items():
        counts: dict[str, int] = {}
        origins: dict[str, str] = {}
        for origin, value in candidates:
            counts[value] = counts.get(value, 0) + 1
            origins.setdefault(value, origin or "")
        login_url = ""
        for candidate in candidates:
            found = ats_of(urlsplit(candidate[0]).netloc, urlsplit(candidate[0]).path)
            if found and found["key"] == key:
                login_url = found["login_url"]
                break

        def score(item):
            value, count = item
            s = count
            origin = origins[value]
            if login_url and origin.rstrip("/") == login_url.rstrip("/"):
                s += 3
            if len(seen_keys.get(value, ())) > 1:
                s -= 2
            return (s, len(value))

        value, _ = max(counts.items(), key=score)
        found_for_key = ats_of(urlsplit(candidates[0][0]).netloc, urlsplit(candidates[0][0]).path)
        picked[key] = {
            "login_id": value,
            "login_id_source": "Chrome保存ログイン",
            "login_url": (found_for_key or {}).get("login_url", ""),
            "home_url": (found_for_key or {}).get("home_url", ""),
        }
    return picked


def login_ids_from_notes() -> dict:
    """手元のメモに書かれたログインIDを拾う。パスワードは拾わない。"""
    found = {}
    pattern = re.compile(r"ログインID[^A-Za-z0-9]*([A-Za-z0-9_-]{5,})")
    for path in PRIVATE.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.finditer(text):
            found.setdefault(match.group(1), path.name)
    return found


def load_manual():
    """手で書いたログインIDやメモ。再収集しても消えない。"""
    if MANUAL_PATH.exists():
        try:
            return json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"sites": []}


def load_existing():
    if MYPAGES_PATH.exists():
        try:
            return json.loads(MYPAGES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"sites": []}


def merge(existing, found, login_ids, id_hints, profiles):
    by_key = {site["key"]: site for site in existing.get("sites", [])}
    for key, row in found.items():
        site = by_key.setdefault(key, {"key": key})
        for field in ("ats", "login_url", "home_url", "official_name"):
            if row.get(field):
                site[field] = row[field]
        site["visits"] = row.get("visits", 0)
        site["last_seen"] = datetime.now().date().isoformat()
    for key, info in login_ids.items():
        site = by_key.setdefault(key, {"key": key})
        site["login_id"] = info["login_id"]
        site["login_id_source"] = info["login_id_source"]
        site.setdefault("ats", key.split(":", 1)[0])
        if info.get("login_url") and not site.get("login_url"):
            site["login_url"] = info["login_url"]
        if info.get("home_url") and not site.get("home_url"):
            site["home_url"] = info["home_url"]
    for manual in load_manual().get("sites", []):
        match = None
        for site in by_key.values():
            names = f"{site.get('company','')} {site.get('official_name','')}"
            if manual.get("company") and manual["company"] in names:
                match = site
                break
        if not match:
            continue
        for field in ("login_id", "login_id_source", "note"):
            if manual.get(field):
                match[field] = manual[field]

    by_key = {k: v for k, v in by_key.items()
              if "not found" not in (v.get("official_name") or "").lower()}

    sites = []
    for site in by_key.values():
        site.setdefault("note", "")
        site.setdefault("login_id", "")
        site.setdefault("login_id_source", "")
        site["ats_label"] = ATS_LABEL.get(site.get("ats", ""), site.get("ats", ""))
        official = OFFICIAL_NAMES.get(site["key"])
        title_name = clean_name(site.get("official_name", ""))
        site["company"] = official or strip_corp(title_name) or site["key"].split(":", 1)[-1]
        sites.append(site)
    sites.sort(key=lambda s: (s.get("company") or "", s["key"]))
    return {
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "source": "Chrome履歴 + Chrome保存ログイン (" + ", ".join(sorted(profiles)) + ")",
        "note": "パスワードは読まないし保存しない。ログインIDはChromeの保存ログインとメモから拾ったものだけ。",
        "login_id_hints": id_hints,
        "sites": sites,
    }


def main():
    ap = argparse.ArgumentParser(description="各社マイページのURLとIDを集める")
    ap.add_argument("--print", action="store_true", help="保存せず一覧を表示する")
    ap.add_argument("--profile", default=None, help="Chromeのプロファイル名を指定する")
    args = ap.parse_args()

    histories = chrome_history_candidates()
    if args.profile:
        histories = [p for p in histories if p.parent.name == args.profile]
    if not histories:
        print("Chromeの履歴が見つかりませんでした。")
        return 1

    found = candidates_from_history(histories)
    login_ids = collect_login_ids(set(found))
    id_hints = login_ids_from_notes()
    profiles = {p.parent.name for p in histories}
    data = merge(load_existing(), found, login_ids, id_hints, profiles)

    with_id = sum(1 for s in data["sites"] if s.get("login_id"))
    print(f"マイページ {len(data['sites'])}件（うちID {with_id}件）")
    for site in data["sites"]:
        extra = f"  ID={site['login_id']}" if site.get("login_id") else ""
        print(f"  {site.get('company',''):<28} {site.get('login_url','')}{extra}")

    if args.print:
        return 0
    MYPAGES_PATH.parent.mkdir(parents=True, exist_ok=True)
    MYPAGES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存しました: {MYPAGES_PATH.relative_to(WORKSPACE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
