"""Runtime configuration shared by development and packaged editions."""

import os
import sys


DEMO_ONLY = os.environ.get("PH_LENDING_DEMO_ONLY", "0") == "1"
APP_NAME = os.environ.get(
    "PH_LENDING_APP_NAME",
    "Lending Pro Freeware",
)
APP_DATA_FOLDER = os.environ.get(
    "PH_LENDING_DATA_FOLDER",
    "PH-Lending Demo" if DEMO_ONLY else "PH-Lending",
)


def get_app_support_dir():
    """Return the edition-specific writable application data directory."""
    override = os.environ.get("PH_LENDING_DATA_DIR")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, APP_DATA_FOLDER)
    if sys.platform == "darwin":
        return os.path.expanduser(
            os.path.join("~", "Library", "Application Support", APP_DATA_FOLDER)
        )
    return os.path.expanduser(os.path.join("~", ".local", "share", APP_DATA_FOLDER))
