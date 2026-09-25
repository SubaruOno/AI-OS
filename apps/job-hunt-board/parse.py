#!/usr/bin/env python3
"""就活の締切データを private/job-hunt/ の Markdown から読み取る。

Markdown は人が読むために書いてあるので、ここでは「読めた行だけ拾う」方針で
解析する。読めなかった行は warnings に退避し、画面には出さない。
元データには一切書き込まない。
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path

YEAR = 2026  # 28卒の応募年。9月/10月など年が書かれていない日付に補う。

SOURCES = [
    {
        "file": "private/job-hunt/2026-09-13/master-deadlines.md",
        "kind": "master",
        "label": "締切マスター",
    },
    {
        "file": "private/job-hunt/2026-09-16/simenavi-update.md",
        "kind": "candidate",
        "label": "締め切りナビ再収集",
    },
]

STATUS_MARKERS = [
    ("✅提出済み", "done", "提出済み"),
    ("✅", "done", "提出済み"),
    ("❌未提出", "missed", "未提出"),
    ("❌不参加", "declined", "不参加"),
]

SOURCE_LABELS = {
    "email": "メール確認済み",
    "navi": "締め切りナビ",
    "mixed": "メール＋ナビ",
}

# 同じ会社を別名で書いているものを重複統合のために寄せる。
FIRM_ALIASES = {
    "アビームコンサルティング": "アビーム",
}

_ROW = re.compile(
    r"^\|\s*(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}:\d{2}))?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$"
)
_PLAIN_ROW = re.compile(
    r"^\|\s*(\d{1,2})/(\d{1,2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$"
)
_BULLET = re.compile(r"^-\s*(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}:\d{2}))?\s+(.+)$")
_MONTH_ONLY = re.compile(r"^-\s*(\d{1,2})月\s+(.+)$")
_CONFLICT_ROW = re.compile(
    r"^\|\s*(.+?)\s*\|\s*(\d{1,2})/(\d{1,2})\s*\|\s*(\d{1,2})/(\d{1,2})"
    r"(?:[\s（(]+([^）)]*)[）)]?)?\s*\|\s*$"
)
_HEADER = re.compile(r"^##\s+(.*)$")
_TAG = re.compile(r"【[^】]*】")


def _make_id(*parts: str) -> str:
    raw = "\u0000".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def clean_title(raw: str):
    """先頭の記号を状態として抜き、強調と【】を落とした見出しを返す。"""
    text = raw.strip()
    status, status_label = "open", ""
    for mark, code, label in STATUS_MARKERS:
        if text.startswith(mark):
            status, status_label = code, label
            text = text[len(mark):].strip()
            break
    important = "**" in text
    text = _TAG.sub("", text.replace("**", "")).strip()
    return text, status, status_label, important


def firm_of(title: str) -> str:
    """見出しの先頭語を会社名の代わりにする。並べ替えと重複統合にだけ使う。"""
    text = title.strip()
    for sep in (" ", "\u3000", "（", "(", "：", ":"):
        at = text.find(sep)
        if 0 < at:
            text = text[:at]
    return FIRM_ALIASES.get(text, text)


def _iso(month: int, day: int, time_text: str | None):
    try:
        d = date(YEAR, month, day)
    except ValueError:
        return None, time_text
    return d.isoformat(), time_text


def _source_from_master(cell: str) -> str:
    text = cell.strip()
    if "メール" in text and "ナビ" in text:
        return "mixed"
    if "メール" in text:
        return "email"
    return "navi"


def _source_from_navi(cell: str) -> str:
    return "email" if "本人宛メール" in cell or "メールでも" in cell else "navi"


def _new_item(*, date_iso, time_text, title, bucket, source, notes, rid, extra=None):
    item = {
        "id": rid,
        "date": date_iso,
        "time": time_text or "",
        "title": title,
        "firm": firm_of(title),
        "bucket": bucket,
        "source": source,
        "source_label": SOURCE_LABELS.get(source, source),
        "notes": notes,
        "status": "open",
        "status_label": "",
        "important": False,
        "conflict": None,
    }
    if extra:
        item.update(extra)
    return item


def _from_master_row(month, day, time_text, title_cell, source_cell):
    title, status, status_label, important = clean_title(title_cell)
    date_iso, time_text = _iso(int(month), int(day), time_text)
    if not date_iso:
        return None
    item = _new_item(
        date_iso=date_iso,
        time_text=time_text,
        title=title,
        bucket="master",
        source=_source_from_master(source_cell),
        notes="",
        rid=_make_id("master", date_iso, title),
    )
    item.update(status=status, status_label=status_label, important=important)
    return item


def parse_master(path: Path):
    items, rules, applied, legend, warnings = [], [], [], [], []
    section = None
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        head = _HEADER.match(line)
        if head:
            section = head.group(1).strip()
            continue

        if line.startswith("- **【"):
            legend.append(line.lstrip("- ").strip())

        if section in ("9月", "10月"):
            m = _ROW.match(line)
            if m:
                item = _from_master_row(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))
                if item:
                    items.append(item)
                else:
                    warnings.append(f"master:{lineno} 日付を読めません: {line}")
                continue

        if section == "11月以降":
            m = _BULLET.match(line)
            if m:
                month, day, time_text, body = m.group(1), m.group(2), m.group(3), m.group(4)
                src = "email" if "【メール確認済み】" in body else "navi"
                item = _from_master_row(month, day, time_text, body, src if src == "navi" else "メール")
                if item:
                    items.append(item)
                else:
                    warnings.append(f"master:{lineno} 日付を読めません: {line}")
                continue
            m = _MONTH_ONLY.match(line)
            if m:
                month = int(m.group(1))
                title, status, status_label, important = clean_title(m.group(2))
                item = _new_item(
                    date_iso=None,
                    time_text="",
                    title=title,
                    bucket="master",
                    source="email",
                    notes=f"{month}月中（日付未確定）",
                    rid=_make_id("master", f"{month}月", title),
                )
                item.update(status=status, status_label=status_label, important=important)
                items.append(item)
                continue

        if section and section.startswith("併願制限"):
            m = re.match(r"^-\s*(.+)$", line)
            if m:
                rules.append(m.group(1).strip())

        if section and section.startswith("既に応募済み"):
            m = re.match(r"^-\s*(.+)$", line)
            if m:
                applied.append(m.group(1).strip())
            elif line and not line.startswith("#") and not line.startswith(">"):
                applied += [part.strip() for part in line.split("、") if part.strip()]

    return items, rules, applied, legend, warnings


def parse_navi(path: Path):
    items, conflicts, warnings = [], [], []
    section = None
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        head = _HEADER.match(line)
        if head:
            section = head.group(1).strip()
            continue
        if not section:
            continue

        if section.startswith("日付が食い違うもの"):
            m = _CONFLICT_ROW.match(line)
            if m:
                g = m.groups()
                title, nm, nd, em, ed, note = g
                email_iso, _ = _iso(int(em), int(ed), "")
                navi_iso, _ = _iso(int(nm), int(nd), "")
                if not email_iso:
                    warnings.append(f"navi:{lineno} 日付を読めません: {line}")
                    continue
                item = _new_item(
                    date_iso=email_iso,
                    time_text="",
                    title=title.strip(),
                    bucket="conflict",
                    source="mixed",
                    notes=(note or "").strip(),
                    rid=_make_id("conflict", title.strip()),
                )
                item["conflict"] = {"navi": navi_iso, "email": email_iso}
                conflicts.append(item)
            continue

        if section in (
            "今日中に判断する候補",
            "9月中の優先候補",
            "10月以降に追加・再確認する候補",
        ):
            m = _PLAIN_ROW.match(line)
            if m:
                month, day, title_raw, note = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4).strip()
                title, status, status_label, important = clean_title(title_raw)
                date_iso, _ = _iso(month, day, "")
                if not date_iso:
                    warnings.append(f"navi:{lineno} 日付を読めません: {line}")
                    continue
                item = _new_item(
                    date_iso=date_iso,
                    time_text="",
                    title=title,
                    bucket="candidate",
                    source=_source_from_navi(note),
                    notes=note,
                    rid=_make_id("navi", date_iso, title),
                )
                item.update(status=status, status_label=status_label, important=important)
                items.append(item)
            continue
    return items, conflicts, warnings


def merge(items):
    """同じ日・同じ会社の重複を1件にまとめる。マスター側を優先して残す。"""
    order, merged = [], {}
    for item in items:
        key = (item["date"] or "", item["firm"])
        if key in merged:
            kept = merged[key]
            sources = sorted(set(kept.get("sources", [kept["source"]]) + [item["source"]]))
            kept["sources"] = sources
            real = [s for s in sources if s != "mixed"]
            if len(real) > 1:
                kept["source"] = "mixed"
            kept["source_label"] = SOURCE_LABELS.get(kept["source"], kept["source"])
            if item["notes"] and item["notes"] not in kept["notes"]:
                kept["notes"] = (kept["notes"] + " / " + item["notes"]).strip(" /")
            if kept["status"] == "open" and item["status"] != "open":
                kept.update(status=item["status"], status_label=item["status_label"])
            kept["important"] = kept["important"] or item["important"]
            if item.get("conflict") and not kept.get("conflict"):
                kept["conflict"] = item["conflict"]
            continue
        item["sources"] = [item["source"]]
        merged[key] = item
        order.append(key)
    return [merged[k] for k in order]


def load(workspace: Path):
    all_items, all_rules, all_applied, legend, warnings = [], [], [], [], []
    for spec in SOURCES:
        path = workspace / spec["file"]
        if not path.exists():
            warnings.append(f"ファイルが見つかりません: {spec['file']}")
            continue
        if spec["kind"] == "master":
            items, rules, applied, legend, warn = parse_master(path)
            all_rules += rules
            all_applied += applied
        else:
            items, conflicts, warn = parse_navi(path)
            all_items += conflicts
        all_items += items
        warnings += warn

    items = merge(all_items)
    items.sort(key=lambda i: (i["date"] or "9999-99-99", i["time"] or "99:99", i["title"]))
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": date.today().isoformat(),
        "items": items,
        "rules": all_rules,
        "applied": all_applied,
        "legend": legend,
        "warnings": warnings,
        "sources": [spec["file"] for spec in SOURCES],
    }


if __name__ == "__main__":
    import json
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
    print(json.dumps(load(root), ensure_ascii=False, indent=2))
