#!/usr/bin/env python3
"""Build a self-contained macOS launcher for PH-Lending Pro."""

import os
import shutil
import stat
import subprocess
import sys


APP_NAME = "PH-Lending Pro"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DEST = os.path.expanduser(f"~/Applications/{APP_NAME}.app")
RUNTIME_DIR = os.path.expanduser("~/Library/Application Support/PH-Lending/runtime")
RUNTIME_PYTHON = os.path.join(RUNTIME_DIR, "bin", "python")
ICNS_PATH = os.path.join(PROJECT_DIR, "icon.icns")
REQUIREMENTS_PATH = os.path.join(PROJECT_DIR, "requirements.txt")

APP_PYTHON_FILES = [
    "app_config.py",
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


def ensure_runtime():
    """Create a local runtime that Finder can access without external-volume TCC."""
    runtime_ok = False
    if os.path.exists(RUNTIME_PYTHON):
        check = subprocess.run(
            [RUNTIME_PYTHON, "-c", "import webview, openpyxl, reportlab, dateutil"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        runtime_ok = check.returncode == 0
    if runtime_ok:
        return

    os.makedirs(os.path.dirname(RUNTIME_DIR), exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", RUNTIME_DIR], check=True)
    subprocess.run(
        [RUNTIME_PYTHON, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    subprocess.run(
        [RUNTIME_PYTHON, "-m", "pip", "install", "-r", REQUIREMENTS_PATH],
        check=True,
    )


def copy_application_code(resources_dir):
    """Copy only runtime files into the application bundle."""
    app_code_dir = os.path.join(resources_dir, "app")
    if os.path.exists(app_code_dir):
        shutil.rmtree(app_code_dir)
    os.makedirs(app_code_dir, exist_ok=True)

    for file_name in APP_PYTHON_FILES:
        shutil.copy2(os.path.join(PROJECT_DIR, file_name), app_code_dir)
    shutil.copy2(REQUIREMENTS_PATH, app_code_dir)
    shutil.copytree(
        os.path.join(PROJECT_DIR, "web"),
        os.path.join(app_code_dir, "web"),
        ignore=shutil.ignore_patterns(".DS_Store"),
    )


def create_app():
    print(f"Building {APP_NAME}.app...")
    ensure_runtime()

    macos_dir = os.path.join(APP_DEST, "Contents", "MacOS")
    resources_dir = os.path.join(APP_DEST, "Contents", "Resources")
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)
    copy_application_code(resources_dir)

    launcher_path = os.path.join(macos_dir, APP_NAME)
    launcher_content = """#!/bin/bash
APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_CODE="$APP_ROOT/Resources/app"
PYTHON="$HOME/Library/Application Support/PH-Lending/runtime/bin/python"
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR"

if [ ! -x "$PYTHON" ]; then
    echo "PH-Lending local runtime is missing. Run create_app_launcher.py again." >> "$LOG_DIR/PH-Lending.log"
    exit 1
fi

cd "$APP_CODE" || exit 1
exec "$PYTHON" "$APP_CODE/main.py" >> "$LOG_DIR/PH-Lending.log" 2>&1
"""
    with open(launcher_path, "w", encoding="utf-8") as launcher:
        launcher.write(launcher_content)
    os.chmod(
        launcher_path,
        stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
    )

    plist_path = os.path.join(APP_DEST, "Contents", "Info.plist")
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleExecutable</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>CFBundleIdentifier</key>
    <string>com.phlending.pro</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1.0</string>
    <key>CFBundleVersion</key>
    <string>2</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>PH-Lending Pro uses the camera to capture client photos.</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>PH-Lending Pro imports client documents selected by the user.</string>
</dict>
</plist>
"""
    with open(plist_path, "w", encoding="utf-8") as plist:
        plist.write(plist_content)

    if os.path.exists(ICNS_PATH):
        shutil.copy2(ICNS_PATH, os.path.join(resources_dir, "icon.icns"))

    subprocess.run(["xattr", "-cr", APP_DEST], check=False)
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", APP_DEST],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(["touch", APP_DEST], check=False)
    print(f"Application installed: {APP_DEST}")


if __name__ == "__main__":
    create_app()
