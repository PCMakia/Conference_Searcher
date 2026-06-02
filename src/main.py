"""US CS Conference Finder — entry point."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_REQUIRED = (
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("lxml", "lxml"),
    ("rapidfuzz", "rapidfuzz"),
    ("sklearn", "scikit-learn"),
    ("yaml", "PyYAML"),
)


def _ensure_dependencies() -> None:
    missing: list[str] = []
    for module, package in _REQUIRED:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if not missing:
        return

    print("Missing Python packages:", ", ".join(missing))
    print()
    print("Install dependencies (recommended):")
    print(f"  cd \"{_ROOT}\"")
    print("  python -m venv .venv")
    print("  .venv\\Scripts\\activate")
    print("  pip install -r requirements.txt")
    print("  python src\\main.py")
    print()
    print("Or run the helper script:")
    print("  .\\run.ps1")
    sys.exit(1)


def main() -> None:
    _ensure_dependencies()
    from src.ui.app import run_app

    run_app()


if __name__ == "__main__":
    main()
