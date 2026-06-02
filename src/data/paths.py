from __future__ import annotations

import sys
from pathlib import Path


def data_dir() -> Path:
    """Return bundled data directory (works in dev and PyInstaller)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "src" / "data"
    return Path(__file__).resolve().parent


def data_file(name: str) -> Path:
    return data_dir() / name
