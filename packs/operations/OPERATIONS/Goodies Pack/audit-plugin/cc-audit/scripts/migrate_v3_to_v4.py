#!/usr/bin/env python3
"""
migrate_v3_to_v4.py — Split a v3 audit-data.json into v4 per-domain files.

Usage:
  python3 migrate_v3_to_v4.py --client-slug <slug> [--dry-run] [--keep-v3-file]

Allowed client slugs: brightside-services, riverside-dental
All other clients are NOT migrated (they stay on v2/v3 indefinitely).

Options:
  --client-slug SLUG   Client slug to migrate (required)
  --dry-run            Show domain sizes without writing
  --keep-v3-file       Keep audit-data.json after migration (default: keep)

Exit codes:
  0 — success
  1 — error
"""

import json
import sys
import shutil
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_reader import is_v3, DOMAIN_ORDER, _compute_checksum


ALLOWED_SLUGS = ["brightside-services", "riverside-dental", "northwind-co", "acme-trades"]

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))
from _paths import get_clients_dir as _get_clients_dir  # noqa: E402


def split_v3_to_domains(v3_data: dict) -> dict[str, dict]:
    """Extract each domain dict from a v3 nested structure."""
    domains = {}
    for domain in DOMAIN_ORDER:
        if domain in v3_data and isinstance(v3_data[domain], dict):
            domains[domain] = v3_data[domain]
        else:
            domains[domain] = {}
    return domains


DOMAIN_WRITERS = {
    "meta": "extractor",
    "extraction": "extractor",
    "findings": "extractor",
    "opportunities": "researcher",
    "strategy": "researcher",
    "architecture": "designer",
}


def build_manifest(slug: str, company_name: str, audit_status: str,
                   domain_checksums: dict[str, str], now: str) -> dict:
    """Build the audit-manifest.json structure."""
    return {
        "_schema_version": "4.0.0",
        "client_slug": slug,
        "company_name": company_name,
        "audit_status": audit_status,
        "updated_at": now,
        "domains": {
            domain: {
                "file": f"{domain}.json",
                "written_by": DOMAIN_WRITERS[domain],
                "updated_at": now,
                "checksum": domain_checksums.get(domain, ""),
            }
            for domain in DOMAIN_ORDER
        },
    }


def print_dry_run(slug: str, domains: dict[str, dict]) -> None:
    """Print domain sizes without writing."""
    print()
    print("DRY RUN — no files will be written")
    print("=" * 60)
    print(f"  Client: {slug}")
    print(f"  Target: v4 multi-file layout")
    print()
    print(f"  {'Domain':<20} {'Keys':<8} {'Size (bytes)':<15} {'File'}")
    print("  " + "-" * 58)
    total = 0
    for domain in DOMAIN_ORDER:
        data = domains.get(domain, {})
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        size = len(content.encode("utf-8"))
        total += size
        print(f"  {domain:<20} {len(data):<8} {size:<15} {domain}.json")
    print("  " + "-" * 58)
    print(f"  {'TOTAL':<20} {'':<8} {total:<15}")
    print()
    print("No files written (--dry-run). Re-run without --dry-run to migrate.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate audit-data.json from v3 nested to v4 multi-file layout."
    )
    parser.add_argument("--client-slug", required=True, metavar="SLUG")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-v3-file", action="store_true", default=True,
                        help="Keep audit-data.json after migration (default: True)")
    args = parser.parse_args()

    slug = args.client_slug

    if slug not in ALLOWED_SLUGS:
        print(
            f"Error: '{slug}' is not in the migration allowlist.\n"
            f"Only these clients can be migrated: {', '.join(ALLOWED_SLUGS)}\n"
            f"Earlier clients stay on v2/v3 indefinitely.",
            file=sys.stderr,
        )
        sys.exit(1)

    audit_dir = _get_clients_dir() / slug / "audit"
    manifest_path = audit_dir / "audit-manifest.json"
    single_path = audit_dir / "audit-data.json"
    backup_path = audit_dir / "audit-data-v3-backup.json"

    if manifest_path.exists():
        print(f"Already on v4 — {slug} has audit-manifest.json.")
        sys.exit(0)

    if not single_path.exists():
        print(f"Error: audit-data.json not found at {single_path}", file=sys.stderr)
        sys.exit(1)

    try:
        v3_data = json.loads(single_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {single_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not is_v3(v3_data):
        print(f"Error: {slug} is on v2 (flat). Migrate to v3 first using migrate_audit_data.py.", file=sys.stderr)
        sys.exit(1)

    domains = split_v3_to_domains(v3_data)

    if args.dry_run:
        print_dry_run(slug, domains)
        sys.exit(0)

    shutil.copy2(single_path, backup_path)
    print(f"Backup saved to {backup_path}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    checksums = {}

    for domain in DOMAIN_ORDER:
        data = domains.get(domain, {})
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        content_bytes = content.encode("utf-8")
        domain_path = audit_dir / f"{domain}.json"
        domain_path.write_bytes(content_bytes)
        checksums[domain] = _compute_checksum(content_bytes)
        size_kb = len(content_bytes) / 1024
        print(f"  Written {domain}.json ({size_kb:.1f} KB)")

    meta = domains.get("meta", {})
    company_name = meta.get("company_name", "")
    audit_status = meta.get("audit_status", "in_progress")

    manifest = build_manifest(slug, company_name, audit_status, checksums, now)

    analyst_meta = v3_data.get("analyst_metadata")
    architect_meta = v3_data.get("architect_metadata")
    if analyst_meta:
        manifest["analyst_metadata"] = analyst_meta
    if architect_meta:
        manifest["architect_metadata"] = architect_meta

    manifest_content = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    manifest_path.write_text(manifest_content)
    print(f"  Written audit-manifest.json")

    print(f"\nMigration complete. {slug} is now on v4.")
    sys.exit(0)


if __name__ == "__main__":
    main()
