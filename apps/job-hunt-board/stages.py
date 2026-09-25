#!/usr/bin/env python3
"""選考ステージの推定とスコア計算。

メールの件名・締切メモ・応募済みメモから、企業ごとに「今どの段階か」を
推定する。推定は決定的なキーワード一致だけで行い、推測で埋めない。
根拠が無い企業は「応募前」のままにする。
"""
from __future__ import annotations

import re

# 段階は 0（浅い）から 4（深い）まで。見送りは -1。
STAGES = [
    (-1, "見送り・選考終了"),
    (0, "応募前"),
    (1, "応募・ES"),
    (2, "適性検査"),
    (3, "面接"),
    (4, "最終・内定"),
]

STAGE_LABEL = {rank: label for rank, label in STAGES}

# 上に書いたものから順に判定し、最も深い段階を採用する。
KEYWORDS = [
    (-1, ["不合格", "不採用", "見送り", "辞退", "選考終了", "ご縁が", "残念ながら"]),
    (4, ["内定", "最終面接", "最終選考", "最終本選考", "オファー"]),
    (3, ["面接", "面談", "interview", "集団討論", "グループディスカッション"]),
    (2, ["適性検査", "WEBテスト", "Webテスト", "ウェブテスト", "SPI", "テストセンター",
         "玉手箱", "TG-WEB", "C-GAB", "WEB適性", "Web適性", "オンライン試験"]),
    (1, ["エントリーシート", "ES", "応募", "エントリー", "提出", "登録完了", "受付完了",
         "予約完了", "本エントリー", "プレエントリー", "選考参加"]),
]

STAGE_POINTS = {-1: 0, 0: 5, 1: 20, 2: 35, 3: 55, 4: 80}
URGENCY_WINDOW = 14  # 締切がこの日数以内だと加点する
URGENCY_PER_DAY = 3


def classify(text: str):
    """文字列から段階を推定する。見つからなければ (None, None)。"""
    if not text:
        return None, None
    best = None
    for rank, words in KEYWORDS:
        for word in words:
            if word in text:
                if best is None or rank > best:
                    best = rank
                break
    if best is None:
        return None, None
    return best, STAGE_LABEL[best]


def deepest(candidates):
    """複数の候補のうち、最も深い段階を返す。"""
    ranks = [rank for rank, _ in candidates if rank is not None]
    if not ranks:
        return 0, STAGE_LABEL[0]
    rank = max(ranks)
    return rank, STAGE_LABEL[rank]


def urgency(days_left):
    """締切までの日数から緊急度を出す。過ぎた締切は加点しない。"""
    if days_left is None or days_left < 0:
        return 0
    return max(0, URGENCY_WINDOW - days_left) * URGENCY_PER_DAY


def score(stage_rank, days_left, mail_count=0):
    points = STAGE_POINTS.get(stage_rank, 0)
    if stage_rank == -1:
        return 0
    return points + urgency(days_left) + min(mail_count, 5)


# ナビサイト・広告・運営事務局。企業からの本物の連絡ではないので信号にしない。
# axol.jp などは企業ATSの直送なので含めない（住友商事などが該当する）。
NOISE_SENDERS = (
    "gakujo.ne.jp", "career-tasu", "careerpark", "rikunabi", "mynavi", "recruit.co.jp",
    "mail.ado", "toeic", "iibc", "shukatsu", "onecareer",
    "offerbox", "jobweb", "キャリアパーク", "就活", "adobe",
)

CORPORATE_SUFFIX = re.compile(r"(株式会社|\(株\)|（株）|ホールディングス|グループ|株式会社様)$")


def is_noise(sender: str, subject: str = "") -> bool:
    """広告・運営事務局からのメールかどうか。差出人だけで判定する。

    件名には「就活」「面接」など普通の語が入るので、件名では判定しない。
    """
    return any(token.lower() in (sender or "").lower() for token in NOISE_SENDERS)


def company_from_mail(sender: str, subject: str) -> str:
    """差出人表示名か件名の【】から企業名を拾う。"""
    m = re.match(r"^[【\[]([^】\]]{2,20})[】\]]", subject.strip())
    if m:
        candidate = m.group(1).strip()
        if not any(x in candidate for x in ("お知らせ", "重要", "ご案内", "締切", "本日")):
            return candidate
    name = re.sub(r"\s*<.*?>\s*$", "", sender or "").strip().strip('"「」『』')
    name = CORPORATE_SUFFIX.sub("", name).strip()
    return name
