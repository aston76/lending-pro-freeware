#!/usr/bin/env python3
"""Run the test suite with the project's virtual environment when available."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def virtualenv_python() -> Path | None:
    """Return the local virtualenv interpreter for macOS/Linux or Windows."""
    candidates = (
        ROOT / ".venv" / "bin" / "python",
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / "venv" / "bin" / "python",
        ROOT / "venv" / "Scripts" / "python.exe",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def pytest_available(python: Path) -> bool:
    result = subprocess.run(
        [str(python), "-c", "import pytest"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    python = virtualenv_python() or Path(sys.executable)
    if not pytest_available(python):
        print(
            "Test dependencies are missing. Run:\n"
            "  python3 -m venv .venv\n"
            "  .venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt\n"
            "On Windows, use .venv\\Scripts\\python.exe instead.",
            file=sys.stderr,
        )
        return 2

    env = os.environ.copy()
    return subprocess.run(
        [str(python), "-m", "pytest", "-q"],
        cwd=ROOT,
        env=env,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
