"""Tiny env helper shared by workspace scripts.

Finds the workspace .env (walking up from this file), loads it once,
and returns variables with a clear error when one is missing.
"""

import os
from pathlib import Path

_loaded = False


def _load_env():
    global _loaded
    if _loaded:
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        _loaded = True
        return  # fall back to plain os.environ
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            break
        current = current.parent
    _loaded = True


def get_env(name: str, required: bool = True) -> str:
    """Return an environment variable, loading .env first. Clear error if missing."""
    _load_env()
    value = os.environ.get(name, "").strip()
    if not value and required:
        raise RuntimeError(
            f"{name} is not set. Add it to the .env file at the workspace root "
            f"(see .env.example for where to get it)."
        )
    return value
