#!/usr/bin/env python3
"""Fast project sanity checks for PH-Lending Pro."""

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = [
    "api.py",
    "backup.py",
    "database.py",
    "demo_generator.py",
    "excel_export.py",
    "loan_engine.py",
    "logger.py",
    "main.py",
    "pdf_generator.py",
]
JS_FILES = [
    "web/app.js",
    "web/components.js",
    "web/print_manager.js",
    "web/pages/alerts.js",
    "web/pages/calendar.js",
    "web/pages/client_detail.js",
    "web/pages/clients.js",
    "web/pages/commissions.js",
    "web/pages/dashboard.js",
    "web/pages/help.js",
    "web/pages/loan_detail.js",
    "web/pages/loans.js",
    "web/pages/logs.js",
    "web/pages/payments.js",
    "web/pages/settings.js",
]


def run_node_checks() -> None:
    node = subprocess.run(
        ["node", "--version"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if node.returncode != 0:
        print("node is required for JavaScript syntax checks.", file=sys.stderr)
        raise SystemExit(1)

    for file_name in JS_FILES:
        subprocess.run(["node", "--check", file_name], cwd=ROOT, check=True)


def main() -> int:
    for name in PYTHON_FILES:
        if not compileall.compile_file(str(ROOT / name), quiet=1, force=True):
            return 1

    run_node_checks()
    print("Project checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
