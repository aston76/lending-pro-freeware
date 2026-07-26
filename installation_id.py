"""Persistent anonymous identifier for one Lending Pro Freeware installation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import uuid

from app_config import get_app_support_dir


INSTALLATION_ID_PATTERN = re.compile(
    r"^LPF-[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
)


def _installation_file() -> Path:
    return Path(get_app_support_dir()) / "installation.json"


def get_installation_id() -> str:
    """Return a stable, anonymous ID stored outside the active loan database."""
    path = _installation_file()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        installation_id = str(payload.get("installation_id", "")).upper()
        if INSTALLATION_ID_PATTERN.fullmatch(installation_id):
            return installation_id
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

    installation_id = f"LPF-{str(uuid.uuid4()).upper()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps({"installation_id": installation_id}, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)
    return installation_id
