#!/usr/bin/env python3
"""締切マスター・追加候補・メールシグナルを1つの feed.json にまとめる。

アプリはこのファイルだけを読む。元データには書き込まない。
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse  # noqa: E402
import stages  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR.parents[1]
DATA_DIR = APP_DIR / "data"
MAIL_PATH = DATA_DIR / "mail.json"
FEED_PATH = DATA_DIR / "feed.json"

CLOSED = {"done", "dismissed", "declined"}


def load_mail():
    if not MAIL_PATH.exists():
        return {"fetched_at": None, "messages": []}
    try:
        return json.loads(MAIL_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"fetched_at": None, "messages": []}


def days_left(iso, today):
    if not iso:
        return None
    return (date.fromisoformat(iso) - today).days


def applied_name(entry: str) -> str:
    return entry.split("（")[0].split("(")[0].strip()


def same_firm(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a == b or (len(a) > 2 and a in b) or (len(b) > 2 and b in a)


def build(workspace=WORKSPACE):
    data = parse.load(workspace)
    mail = load_mail()
    today = date.today()

    known = sorted({item["firm"] for item in data["items"]})
    mails_by_company = {}
    for message in mail.get("messages", []):
        company = message.get("company") or ""
        mails_by_company.setdefault(company, []).append(message)

    grouped = {}
    for item in data["items"]:
        grouped.setdefault(item["firm"], []).append(item)

    names = set(grouped) | set(mails_by_company)
    companies = []
    for name in names:
        items = sorted(grouped.get(name, []), key=lambda i: (i["date"] or "9999", i["time"] or "99"))
        mails = mails_by_company.get(name, [])

        # 状態は item 側のユーザー記録とマークダウンの両方を見る
        open_items = [i for i in items if i["status"] not in CLOSED]
        upcoming = [i for i in open_items if i["date"] and days_left(i["date"], today) >= 0]
        next_item = upcoming[0] if upcoming else (open_items[0] if open_items else None)
        overdue = [i for i in open_items if i["date"] and days_left(i["date"], today) < 0]

        candidates = []
        for item in items:
            rank, _ = stages.classify(f"{item['title']} {item['notes']}")
            candidates.append((rank, None))
        for entry in data["applied"]:
            if same_firm(name, applied_name(entry)):
                rank, _ = stages.classify(entry)
                candidates.append((rank if rank is not None else 1, None))
        for message in mails:
            candidates.append((message.get("signal_rank"), None))

        stage_rank, stage_label = stages.deepest(candidates)
        left = days_left(next_item["date"], today) if next_item and next_item["date"] else None
        companies.append({
            "name": name,
            "stage_rank": stage_rank,
            "stage": stage_label,
            "score": stages.score(stage_rank, left, len(mails)),
            "next": ({
                "date": next_item["date"],
                "time": next_item["time"],
                "title": next_item["title"],
                "source": next_item["source"],
                "status": next_item["status"],
                "days_left": left,
                "id": next_item["id"],
            } if next_item else None),
            "open_count": len(open_items),
            "overdue_count": len(overdue),
            "mail_count": len(mails),
            "mails": mails[:5],
            "items": [i["id"] for i in items],
        })

    companies.sort(key=lambda c: (
        -c["score"],
        c["next"]["date"] if c["next"] and c["next"]["date"] else "9999-99-99",
        c["name"],
    ))
    for index, company in enumerate(companies, 1):
        company["rank"] = index

    feed = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "mail_fetched_at": mail.get("fetched_at"),
        "mail_count": len(mail.get("messages", [])),
        "companies": companies,
        "items": data["items"],
        "rules": data["rules"],
        "applied": data["applied"],
        "legend": data["legend"],
        "warnings": data["warnings"],
        "sources": data["sources"],
    }
    return feed


def write(feed, path=FEED_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main():
    feed = build()
    path = write(feed)
    print(f"企業 {len(feed['companies'])}件 / 締切 {len(feed['items'])}件 → {path.relative_to(WORKSPACE)}")
    for company in feed["companies"][:12]:
        nxt = company["next"]
        when = f"{nxt['date']} ({nxt['days_left']}日)" if nxt else "-"
        print(f"  {company['rank']:>2}. {company['score']:>3}pt {company['stage']:<10} {company['name']:<16} {when}")
    if feed["warnings"]:
        print("警告:", feed["warnings"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
