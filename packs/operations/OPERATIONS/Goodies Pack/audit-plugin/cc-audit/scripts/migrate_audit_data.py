#!/usr/bin/env python3
"""
migrate_audit_data.py — Migrate an audit-data.json file from v2 flat to v3 nested structure.

Usage:
  python3 migrate_audit_data.py --client-slug <slug> [--dry-run]

Allowed client slugs: brightside-services, riverside-dental
All other clients are NOT migrated (they stay on v2 indefinitely).

Options:
  --client-slug SLUG   Client slug to migrate (required)
  --dry-run            Show what would change without writing

Exit codes:
  0 — success (migrated, already on v3, or dry-run completed)
  1 — error (file not found, client not in allowed list, invalid JSON)
"""

import json
import sys
import shutil
import argparse
import warnings
from pathlib import Path

# Allow import from same directory
sys.path.insert(0, str(Path(__file__).parent))
from audit_reader import nest, is_v3, DOMAIN_ROUTING, META_KEYS, ROOT_KEYS, DROP_KEYS
from _paths import get_clients_dir as _get_clients_dir


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

ALLOWED_SLUGS = ["brightside-services", "riverside-dental", "northwind-co", "acme-trades"]


# ---------------------------------------------------------------------------
# Domain routing helper
# ---------------------------------------------------------------------------

def classify_key(key: str) -> str:
    """Return the destination domain string for a flat v2 key."""
    if key in DROP_KEYS:
        return "DROP"
    if key in ROOT_KEYS:
        return "root"
    if key == "constraints" or key == "strategic_notes":
        return "extraction.client_context (sub-key)"
    if key == "business_metrics_list":
        return "extraction.business_metrics (merge/discard)"
    if key in DOMAIN_ROUTING:
        return DOMAIN_ROUTING[key]
    if key in META_KEYS:
        return "meta"
    return "meta (unknown — defaulting)"


# ---------------------------------------------------------------------------
# Dry-run summary
# ---------------------------------------------------------------------------

def print_dry_run_summary(flat: dict) -> None:
    """Print a table showing which key moves to which domain."""
    # Group keys by destination domain
    groups: dict[str, list[str]] = {}
    for key in flat:
        dest = classify_key(key)
        groups.setdefault(dest, []).append(key)

    print()
    print("DRY RUN — no files will be written")
    print("=" * 60)
    print(f"  Source keys: {len(flat)}")
    print(f"  Current _schema_version: {flat.get('_schema_version', 'not set')}")
    print(f"  Target _schema_version: 3.0.0")
    print()
    print(f"  {'Destination':<40} {'Keys':}")
    print("  " + "-" * 58)

    domain_order = [
        "root",
        "meta",
        "extraction",
        "extraction.client_context (sub-key)",
        "extraction.business_metrics (merge/discard)",
        "findings",
        "opportunities",
        "strategy",
        "architecture",
        "DROP",
        "meta (unknown — defaulting)",
    ]

    for dest in domain_order:
        if dest in groups:
            keys = groups[dest]
            # Print first key on same line as destination, rest indented
            first = keys[0]
            rest = keys[1:]
            print(f"  {dest:<40} {first}")
            for k in rest:
                print(f"  {'':<40} {k}")

    # Any destination not in our ordered list
    for dest in sorted(groups):
        if dest not in domain_order:
            for k in groups[dest]:
                print(f"  {dest:<40} {k}")

    print()
    print("No files written (--dry-run). Re-run without --dry-run to migrate.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate audit-data.json from v2 flat to v3 nested structure."
    )
    parser.add_argument(
        "--client-slug",
        required=True,
        metavar="SLUG",
        help="Client slug to migrate (e.g. brightside-services)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files",
    )
    args = parser.parse_args()

    slug = args.client_slug

    # Enforce allowlist
    if slug not in ALLOWED_SLUGS:
        print(
            f"Error: '{slug}' is not in the migration allowlist.\n"
            f"Only these clients can be migrated: {', '.join(ALLOWED_SLUGS)}\n"
            f"Earlier clients stay on v2 indefinitely — the flattener handles them transparently.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve paths via Drive-aware helper
    audit_dir = _get_clients_dir() / slug / "audit"
    audit_path = audit_dir / "audit-data.json"
    backup_path = audit_dir / "audit-data-v2-backup.json"

    if not audit_path.exists():
        print(f"Error: audit-data.json not found at {audit_path}", file=sys.stderr)
        sys.exit(1)

    # Load and parse
    try:
        flat = json.loads(audit_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {audit_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    # Already v3?
    if is_v3(flat):
        print(f"Already on v3 — {slug} does not need migration.")
        sys.exit(0)

    # Dry-run mode
    if args.dry_run:
        print_dry_run_summary(flat)
        sys.exit(0)

    # Create backup before any write
    shutil.copy2(audit_path, backup_path)
    print(f"Backup saved to {backup_path}")

    # Convert to v3
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        nested = nest(flat)

    # Surface any warnings from nest()
    for w in caught_warnings:
        print(f"Warning: {w.message}", file=sys.stderr)

    # Write v3 file (overwrite)
    audit_path.write_text(json.dumps(nested, indent=2, ensure_ascii=False) + "\n")
    print(f"Migration complete. {slug} is now on v3.")
    sys.exit(0)


if __name__ == "__main__":
    main()
