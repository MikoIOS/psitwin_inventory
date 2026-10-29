"""Stable paths after splitting the repository into backend and frontend."""
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_ROOT.parent


def runtime_path(value: str) -> Path:
    """Prefer backend-local files, retaining existing root-level models/venvs."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    local = BACKEND_ROOT / path
    legacy = REPOSITORY_ROOT / path
    if local.exists():
        return local
    if legacy.exists():
        return legacy
    # Keep new cache files alongside an existing root-level environment.
    if path.parts and (REPOSITORY_ROOT / path.parts[0]).exists():
        return legacy
    return local
