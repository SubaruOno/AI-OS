#!/usr/bin/env python3
"""
backfill_source_documents.py — Find the source file for extracted items that lost their
attribution.

For every waste_item / pain_point / optimisation / process step that has a source_quote
but no source_document, walk all transcript-like files in the client directory and
fuzzy-match the quote. When a single high-confidence match is found, set source_document
(and source_session + source_timestamp_seconds if the match is a Fathom transcript).
Ambiguous or unmatched items are logged to backfill-report.json for manual review —
never auto-picked.

Usage:
  python3 apg-audit-plugin/scripts/backfill_source_documents.py --slug <slug> [--dry-run] [--threshold 0.85]

Exits 0 always; the report file is the source of truth.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

THIS = Path(__file__).resolve()
SCRIPTS_DIR = THIS.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from audit_reader import load_all, save_domain  # noqa: E402
from _paths import get_clients_dir as _get_clients_dir, get_client_subdir  # noqa: E402

REPO_ROOT = Path.cwd()
DEFAULT_THRESHOLD = 0.85
MIN_QUOTE_LEN_FOR_MATCH = 25
MAX_QUOTE_LEN_FOR_MATCH = 280


TIMESTAMP_RE = re.compile(r"\[(\d{1,3}):(\d{2})(?::(\d{2}))?\]")


def _parse_timestamp(line: str) -> int | None:
    m = TIMESTAMP_RE.search(line)
    if not m:
        return None
    a, b, c = m.groups()
    if c is not None:
        return int(a) * 3600 + int(b) * 60 + int(c)
    return int(a) * 60 + int(b)


def _normalize_for_match(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_fathom_transcript(path: Path, client_dir: Path) -> bool:
    rel = path.relative_to(client_dir)
    return rel.parts[:1] in (("meetings",), ("01-meetings",)) and path.name == "transcript.txt"


def _collect_candidate_files(client_dir: Path) -> list[Path]:
    """All files that could contain a source quote. Fathom transcripts first (preferred when
    multiple files match), then Loom + admin markdown."""
    out: list[Path] = []
    meetings = client_dir / "01-meetings"
    if not meetings.is_dir():
        meetings = client_dir / "meetings"
    if meetings.is_dir():
        for p in sorted(meetings.glob("*/transcript.txt")):
            out.append(p)
    materials = client_dir / "02-materials"
    if not materials.is_dir():
        materials = client_dir / "client-provided-materials"
    if materials.is_dir():
        for p in sorted(materials.rglob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() in {".md", ".txt"}:
                out.append(p)
    return out


def _build_session_lookup(extraction: dict) -> dict[str, dict]:
    """Map meeting folder name → session record (for setting source_session)."""
    by_folder: dict[str, dict] = {}
    for s in (extraction.get("sessions") or []):
        folder = s.get("folder") or s.get("meeting_folder", "")
        if folder:
            # Both bare folder name and "meetings/<folder>" path forms accepted
            by_folder[folder] = s
            by_folder[f"meetings/{folder}"] = s
    return by_folder


def _quote_fragments(quote_norm: str) -> list[str]:
    """Multiple sub-quotes to try matching against. Transcripts split a long quote across
    several speaker-turn lines, so a single contiguous match against the whole quote often
    falls below threshold. We try the longest stretches in priority order."""
    fragments: list[str] = []
    fragments.append(quote_norm)
    # First sentence (up to a period)
    end = quote_norm.find(" period ")  # normalize stripped punctuation — fall back below
    if "." in quote_norm:  # safety
        pass
    # Re-split on the un-normalized boundary heuristic: chunks of 60+ chars
    chunk_size = 80
    if len(quote_norm) > chunk_size:
        # Pick the longest 80-char window from the start (high signal, no transcript splits)
        fragments.append(quote_norm[:chunk_size])
        if len(quote_norm) > chunk_size * 2:
            mid = len(quote_norm) // 2
            fragments.append(quote_norm[mid - chunk_size // 2: mid + chunk_size // 2])
    return fragments


def _score_file(file_text: str, quote_norm: str, file_text_norm: str) -> tuple[float, int]:
    """Return (ratio, char_index_in_original_text). Ratio in [0, 1], -1 if too short.

    Tries multiple sub-quotes and returns the best match — transcripts often split a
    multi-sentence quote across separate `[MM:SS]` speaker-turn lines, breaking a single
    contiguous SequenceMatcher pass. The ratio is computed relative to the sub-quote that
    matched, since matching a sub-fragment with high confidence is sufficient to locate
    the source file (and the matched line gives us the timestamp anchor).
    """
    if len(quote_norm) < MIN_QUOTE_LEN_FOR_MATCH:
        return (-1.0, -1)
    best_ratio = 0.0
    best_idx = -1
    for frag in _quote_fragments(quote_norm):
        if len(frag) < MIN_QUOTE_LEN_FOR_MATCH:
            continue
        sm = SequenceMatcher(None, file_text_norm, frag, autojunk=False)
        match = sm.find_longest_match(0, len(file_text_norm), 0, len(frag))
        if match.size == 0:
            continue
        ratio = match.size / max(len(frag), 1)
        if ratio > best_ratio:
            best_ratio = ratio
            # Map normalized offset back to the original by simple proportion.
            best_idx = int(match.a * len(file_text) / max(len(file_text_norm), 1))
    return (best_ratio, best_idx)


def _line_at(file_text: str, char_idx: int) -> tuple[str, int]:
    """Return (line, line_number) at the given character offset."""
    if char_idx < 0:
        return ("", 0)
    line_start = file_text.rfind("\n", 0, char_idx) + 1
    line_end = file_text.find("\n", char_idx)
    if line_end == -1:
        line_end = len(file_text)
    line = file_text[line_start:line_end]
    line_number = file_text.count("\n", 0, line_start) + 1
    return (line, line_number)


def _resolve_for_match_against_fathom(matched_line: str, file_path: Path, client_dir: Path,
                                       session_lookup: dict) -> dict:
    """Pull session_number + timestamp_seconds from a Fathom transcript line."""
    out: dict = {}
    rel = file_path.relative_to(client_dir)
    parts = rel.parts  # e.g. ("01-meetings", "2026-04-22-jordan-and-adam", "transcript.txt")
    if len(parts) >= 2 and parts[0] in ("meetings", "01-meetings"):
        folder = parts[1]
        s = session_lookup.get(folder) or session_lookup.get(f"meetings/{folder}") or session_lookup.get(f"01-meetings/{folder}")
        if s and isinstance(s.get("session_number"), int):
            out["source_session"] = s["session_number"]
    ts = _parse_timestamp(matched_line)
    if ts is not None:
        out["source_timestamp_seconds"] = ts
    return out


def _relative_source_doc(file_path: Path, client_dir: Path) -> str:
    rel = file_path.relative_to(client_dir)
    parts = rel.parts
    # For materials, drop the folder prefix to match the convention used in audit-data
    # (the renderer's _resolve_doc_href strips "client-provided-materials/" anyway).
    if parts and parts[0] in ("02-materials", "client-provided-materials"):
        rel = Path(*parts[1:])
    return str(rel).replace("\\", "/")


def _try_backfill_item(item: dict, files: list[Path], file_texts: dict[Path, tuple[str, str]],
                       client_dir: Path, session_lookup: dict,
                       threshold: float) -> tuple[str, list[dict]]:
    """Return (outcome, candidates).

    outcome ∈ {"unfixable", "matched", "ambiguous", "no_match"}.
    candidates is the list of {path, score, line, ts} sorted by score desc.
    """
    quote = (item.get("source_quote") or item.get("quote") or "").strip()
    if not quote:
        return ("unfixable", [])
    # Truncate very long quotes — only the first 280 chars need to match
    quote_for_match = quote[:MAX_QUOTE_LEN_FOR_MATCH]
    quote_norm = _normalize_for_match(quote_for_match)
    if len(quote_norm) < MIN_QUOTE_LEN_FOR_MATCH:
        return ("unfixable", [])

    candidates: list[dict] = []
    for fp in files:
        text, text_norm = file_texts[fp]
        ratio, orig_idx = _score_file(text, quote_norm, text_norm)
        if ratio >= threshold:
            line, line_no = _line_at(text, orig_idx)
            candidates.append({
                "path": fp,
                "score": ratio,
                "line": line,
                "line_no": line_no,
                "is_fathom": _is_fathom_transcript(fp, client_dir),
            })
    candidates.sort(key=lambda c: (-c["score"], not c["is_fathom"]))
    if not candidates:
        return ("no_match", [])

    # Conservative resolution rules:
    #   • Exactly one candidate                          → matched
    #   • Best score ≥ 0.99 AND gap to runner-up ≥ 0.15 → matched (near-exact wins)
    #   • Otherwise                                       → ambiguous (manual review)
    if len(candidates) == 1:
        outcome = "matched"
    else:
        top, runner = candidates[0], candidates[1]
        if top["score"] >= 0.99 and (top["score"] - runner["score"]) >= 0.15:
            outcome = "matched"
        else:
            outcome = "ambiguous"

    return (outcome, candidates)


def _apply_match(item: dict, candidate: dict, client_dir: Path, session_lookup: dict) -> None:
    fp: Path = candidate["path"]
    item["source_document"] = _relative_source_doc(fp, client_dir)
    if candidate["is_fathom"]:
        fathom_fields = _resolve_for_match_against_fathom(
            candidate["line"], fp, client_dir, session_lookup
        )
        for k, v in fathom_fields.items():
            # Don't overwrite existing values
            if item.get(k) in (None, "", 0) and v is not None:
                item[k] = v


def _iter_targets(audit_flat: dict):
    """Yield (collection_name, item_dict, item_id) for every item missing source_document.

    For process steps, item is the inner step dict; collection_name is `processes`.
    """
    for w in (audit_flat.get("waste_items") or []):
        if not w.get("source_document"):
            yield ("waste_items", w, w.get("waste_id") or w.get("activity", "")[:30])
    for p in (audit_flat.get("pain_points") or []):
        if not p.get("source_document"):
            yield ("pain_points", p, p.get("pain_point_id") or "")
    for o in (audit_flat.get("optimisations") or []):
        if not o.get("source_document"):
            yield ("optimisations", o, o.get("optimisation_id") or "")
    for proc in (audit_flat.get("processes") or []):
        for step in (proc.get("steps") or []):
            if not step.get("source_document"):
                yield ("processes", step, step.get("step_id") or "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--dry-run", action="store_true", help="Compute matches but do not write")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="Minimum SequenceMatcher ratio to consider a candidate (default 0.85)")
    args = ap.parse_args()

    slug = args.slug
    client_dir = _get_clients_dir() / slug
    if not client_dir.is_dir():
        print(f"ERROR: client directory not found: {client_dir}", file=sys.stderr)
        return 1

    audit = load_all(slug)
    session_lookup = _build_session_lookup(audit)

    files = _collect_candidate_files(client_dir)
    if not files:
        print(f"No transcript-like files found under {client_dir}/meetings or "
              f"{client_dir}/client-provided-materials — nothing to match against.",
              file=sys.stderr)
        return 0
    file_texts: dict[Path, tuple[str, str]] = {}
    for fp in files:
        try:
            t = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  skip {fp}: {e}", file=sys.stderr)
            continue
        file_texts[fp] = (t, _normalize_for_match(t))

    summary: dict[str, dict[str, int]] = defaultdict(lambda: {
        "orphans": 0, "matched": 0, "ambiguous": 0, "no_match": 0, "unfixable": 0,
    })
    report: list[dict] = []

    for collection, item, item_id in _iter_targets(audit):
        summary[collection]["orphans"] += 1
        outcome, candidates = _try_backfill_item(item, files, file_texts, client_dir,
                                                 session_lookup, args.threshold)
        summary[collection][outcome] += 1

        if outcome == "matched":
            chosen = candidates[0]
            _apply_match(item, chosen, client_dir, session_lookup)
            report.append({
                "outcome": "matched",
                "collection": collection,
                "item_id": item_id,
                "matched_to": str(chosen["path"].relative_to(REPO_ROOT)),
                "score": round(chosen["score"], 3),
                "line_no": chosen["line_no"],
                "is_fathom": chosen["is_fathom"],
                "set_fields": {
                    "source_document": item.get("source_document"),
                    "source_session": item.get("source_session"),
                    "source_timestamp_seconds": item.get("source_timestamp_seconds"),
                },
            })
        else:
            report.append({
                "outcome": outcome,
                "collection": collection,
                "item_id": item_id,
                "quote_preview": ((item.get("source_quote") or item.get("quote") or "")[:120]),
                "top_candidates": [
                    {
                        "path": str(c["path"].relative_to(REPO_ROOT)),
                        "score": round(c["score"], 3),
                        "line_no": c["line_no"],
                        "is_fathom": c["is_fathom"],
                    }
                    for c in candidates[:3]
                ],
            })

    # Write report
    report_path = client_dir / "audit" / "backfill-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({
        "slug": slug,
        "threshold": args.threshold,
        "dry_run": args.dry_run,
        "summary": summary,
        "entries": report,
    }, indent=2, default=str), encoding="utf-8")

    # Persist updates
    if not args.dry_run:
        # Build a set of collections we touched (matched or modified)
        touched_in_findings = any(e["outcome"] == "matched" and e["collection"] in
                                  {"waste_items", "pain_points", "optimisations"} for e in report)
        touched_in_extraction = any(e["outcome"] == "matched" and e["collection"] == "processes"
                                    for e in report)
        if touched_in_findings:
            findings_dict = {k: audit.get(k) for k in (
                "pain_points", "pain_points_summary", "optimisations", "waste_items",
                "contradictions", "follow_up_questions", "follow_up_summary",
                "completeness_checklist", "change_readiness", "objections",
                "positive_signals", "data_gaps",
            ) if k in audit}
            save_domain(slug, "findings", findings_dict)
        if touched_in_extraction:
            extraction_dict = {k: audit.get(k) for k in (
                "processes", "decision_nodes", "tools", "staff_roster",
                "business_metrics", "business_metrics_list", "business_stages_covered",
                "sessions", "extracted_materials", "client_context",
            ) if k in audit}
            save_domain(slug, "extraction", extraction_dict)

    # Print human summary
    print(f"BACKFILL {'(DRY RUN) ' if args.dry_run else ''}COMPLETE — {slug}")
    for col in ("waste_items", "pain_points", "optimisations", "processes"):
        s = summary.get(col)
        if not s or s["orphans"] == 0:
            continue
        print(f"  {col:14s}: {s['orphans']:3d} orphans → "
              f"{s['matched']} backfilled, {s['ambiguous']} manual review, "
              f"{s['no_match']} no match, {s['unfixable']} unfixable")
    print(f"Report: {report_path.relative_to(REPO_ROOT)}")
    if args.dry_run:
        print("(dry-run — no audit files modified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
