#!/usr/bin/env python3
"""
Portable path resolution for the Bosar Audit Plugin.

All scripts import from here instead of hard-coding repo-relative paths.

Resolution order for clients_dir:
  1. config.yaml paths.clients_dir override (set by /audit:0-setup)
  2. Monorepo auto-detect: {plugin-root}/../clients/
  3. Standalone fallback: {plugin-root}/clients/

IMPORTANT: This module must not import any other plugin script module.
Stdlib + PyYAML only.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PLUGIN_ROOT / "config.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    text = CONFIG_PATH.read_text()
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        return _parse_config_fallback(text)


def _parse_config_fallback(text: str) -> dict:
    """Minimal parser used when PyYAML is unavailable: recovers the flat keys
    this module needs (paths.clients_dir, paths.client_paths.*)."""
    import re
    cfg: dict = {"paths": {"clients_dir": "", "client_paths": {}}}
    section = None
    for line in text.splitlines():
        if re.match(r"^\s*#", line) or not line.strip():
            continue
        if re.match(r"^paths:\s*$", line):
            section = "paths"
            continue
        if re.match(r"^\S", line):
            section = None
        m = re.match(r'^\s+clients_dir:\s*"?([^"#]*)"?\s*(#.*)?$', line)
        if section == "paths" and m:
            cfg["paths"]["clients_dir"] = m.group(1).strip()
        m = re.match(r'^\s+([\w-]+):\s*"([^"]+)"\s*$', line)
        if section == "paths" and m and m.group(1) not in ("clients_dir", "client_paths"):
            cfg["paths"]["client_paths"][m.group(1)] = m.group(2)
    return cfg


def _paths_cfg() -> dict:
    return load_config().get("paths") or {}


@lru_cache(maxsize=1)
def _detect_monorepo() -> bool:
    parent = PLUGIN_ROOT.parent
    return (parent / "clients").is_dir() or (parent / "apg-sales-plugin").is_dir()


def _project_root() -> Optional[Path]:
    return PLUGIN_ROOT.parent if _detect_monorepo() else None


def get_clients_dir() -> Path:
    override = _paths_cfg().get("clients_dir", "").strip()
    if override:
        return Path(override).expanduser()
    pr = _project_root()
    if pr:
        return pr / "clients"
    return PLUGIN_ROOT / "clients"


def get_client_path(slug: str) -> Path:
    # Check per-client path overrides first (set by skill for clients in non-standard folders)
    overrides = _paths_cfg().get("client_paths") or {}
    if slug in overrides:
        override_path = Path(overrides[slug]).expanduser()
        if override_path.exists():
            return override_path
    return get_clients_dir() / slug


def get_clients_json_path() -> Path:
    return get_clients_dir() / "clients.json"


# Canonical subfolder names -> ordered legacy fallback names.
# New canonical names reflect the v2 folder structure.
# Legacy canonical names (01-meetings, 02-materials, etc.) are kept for
# backward compatibility so existing callers continue to resolve correctly.
_SUBFOLDER_ALIASES: dict[str, list[str]] = {
    # ── New canonical names (use these in new code) ──────────────────────────
    "01-materials/meetings":  ["01-meetings", "meetings"],
    "01-materials/documents": ["02-materials", "client-provided-materials"],
    "01-materials/emails":    ["emails", "follow-up-emails", "follow-up"],
    "02-sales":               ["03-sales", "close-page"],
    "03-audit":               [],
    "03-audit/data":          ["audit"],
    "03-audit/deliverables":  ["deliverables"],
    "03-audit/prototype":     ["prototype"],
    "03-audit/reviews":       ["reviews"],
    "03-audit/handoff":       ["_handoff"],
    "03-audit/sessions":      [],
    "00-admin":               [],
    "_archive":               [],
    # ── Legacy canonical names (backward compat for existing callers) ────────
    "01-meetings":  ["01-materials/meetings", "meetings"],
    "02-materials": ["01-materials/documents", "client-provided-materials"],
    "03-sales":     ["02-sales", "close-page"],
    "emails":       ["01-materials/emails", "follow-up-emails", "follow-up"],
    "_handoff":     ["03-audit/handoff"],
}


def get_client_subdir(slug: str, name: str) -> Path:
    """Resolve a client subdirectory by canonical name, falling back to legacy names.

    Handles multi-level names like '03-audit/data' correctly.
    """
    client = get_client_path(slug)
    primary = client / name
    if primary.exists():
        return primary
    for fallback in _SUBFOLDER_ALIASES.get(name, []):
        legacy = client / fallback
        if legacy.exists():
            return legacy
    return primary


def get_audit_data_dir(slug: str) -> Path:
    """Return the audit data directory: 03-audit/data/ (fallback: audit/)."""
    return get_client_subdir(slug, "03-audit/data")


def get_audit_deliverables_dir(slug: str) -> Path:
    """Return the audit deliverables directory: 03-audit/deliverables/ (fallback: deliverables/)."""
    return get_client_subdir(slug, "03-audit/deliverables")


def get_audit_sessions_dir(slug: str) -> Path:
    """Return the audit sessions directory: 03-audit/sessions/."""
    return get_client_subdir(slug, "03-audit/sessions")


def get_engagement_path(slug: str, engagement_slug: str) -> Path:
    """Resolve an engagement folder: numbered root (04-slug) or legacy delivery/slug."""
    client = get_client_path(slug)
    for entry in sorted(client.iterdir()):
        if entry.is_dir() and entry.name.endswith(f"-{engagement_slug}"):
            prefix = entry.name.split("-")[0]
            if prefix.isdigit() and int(prefix) >= 4:
                return entry
    legacy = client / "delivery" / engagement_slug
    if legacy.exists():
        return legacy
    return client / f"0{next_engagement_number(slug)}-{engagement_slug}"


def next_engagement_number(slug: str) -> int:
    """Return the next sequential engagement number (minimum 4)."""
    client = get_client_path(slug)
    max_num = 3
    try:
        for entry in client.iterdir():
            if entry.is_dir() and len(entry.name) >= 2 and entry.name[:2].isdigit():
                max_num = max(max_num, int(entry.name[:2]))
    except (OSError, ValueError):
        pass
    return max_num + 1


def ensure_available(path: Path, label: str = "") -> None:
    """Raise a clear error if a file is not locally available."""
    if not path.exists():
        clients_dir = get_clients_dir()
        drive_hint = ""
        try:
            path.relative_to(clients_dir)
            drive_hint = (
                " This file may not be downloaded from Google Drive yet. "
                "Open Google Drive for Desktop and ensure the file is available offline, "
                "or click the file in Drive to trigger a download."
            )
        except ValueError:
            pass
        name = label or str(path)
        raise FileNotFoundError(f"File not found: {name}\n  Path: {path}{drive_hint}")


if __name__ == "__main__":
    mode = "monorepo" if _detect_monorepo() else "standalone"
    print(f"Mode:        {mode}")
    print(f"PLUGIN_ROOT: {PLUGIN_ROOT}")
    clients = get_clients_dir()
    print(f"clients_dir: {clients}  {'exists' if clients.exists() else 'MISSING'}")
    cj = get_clients_json_path()
    print(f"clients.json:{cj}  {'exists' if cj.exists() else 'MISSING'}")
