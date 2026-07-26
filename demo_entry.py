"""PyInstaller entry point for the isolated demo-only macOS edition."""

import multiprocessing
import os


os.environ.setdefault("PH_LENDING_DEMO_ONLY", "1")
# Keep the existing data folder for backward-compatible upgrades.
os.environ.setdefault("PH_LENDING_APP_NAME", "Lending Pro Freeware")
os.environ.setdefault("PH_LENDING_DATA_FOLDER", "PH-Lending Demo")

from main import main


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
