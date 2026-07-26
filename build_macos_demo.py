#!/usr/bin/env python3
"""Build the self-contained Apple Silicon demo app and distributable DMG."""

import hashlib
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys


PROJECT_DIR = Path(__file__).resolve().parent
APP_NAME = "PH-Lending Pro Demo"
BUNDLE_ID = "com.phlending.pro.demo"
ARCHITECTURE = "arm64"
BUILD_DIR = PROJECT_DIR / "build" / "macos-demo"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "work"
SPEC_DIR = BUILD_DIR / "spec"
DMG_STAGE = BUILD_DIR / "dmg"
RELEASE_DIR = PROJECT_DIR / "release"
APP_PATH = DIST_DIR / f"{APP_NAME}.app"
DMG_PATH = RELEASE_DIR / f"PH-Lending-Pro-Demo-macOS-{ARCHITECTURE}.dmg"
CHECKSUM_PATH = Path(str(DMG_PATH) + ".sha256")


def run(command):
    print("+", " ".join(str(part) for part in command))
    subprocess.run([str(part) for part in command], check=True, cwd=PROJECT_DIR)


def verify_host():
    if sys.platform != "darwin":
        raise RuntimeError("The macOS application must be built on macOS.")
    if platform.machine() != ARCHITECTURE:
        raise RuntimeError("This release script currently builds Apple Silicon only.")


def build_app():
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    for directory in (DIST_DIR, WORK_DIR, SPEC_DIR, RELEASE_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--osx-bundle-identifier",
        BUNDLE_ID,
        "--target-architecture",
        ARCHITECTURE,
        "--distpath",
        DIST_DIR,
        "--workpath",
        WORK_DIR,
        "--specpath",
        SPEC_DIR,
        "--add-data",
        f"{PROJECT_DIR / 'web'}:web",
        "--hidden-import",
        "cv2",
        "--hidden-import",
        "webview.platforms.cocoa",
    ]
    icon = PROJECT_DIR / "icon.icns"
    if icon.exists():
        command.extend(["--icon", icon])
    command.append(PROJECT_DIR / "demo_entry.py")
    run(command)

    info_path = APP_PATH / "Contents" / "Info.plist"
    with info_path.open("rb") as handle:
        info = plistlib.load(handle)
    info.update({
        "CFBundleDisplayName": APP_NAME,
        "CFBundleName": APP_NAME,
        "CFBundleShortVersionString": "1.1.0",
        "CFBundleVersion": "3",
        "LSMinimumSystemVersion": "12.0",
        "NSCameraUsageDescription": "PH-Lending Pro Demo uses the camera to capture demo client photos.",
        "NSPhotoLibraryUsageDescription": "PH-Lending Pro Demo imports files selected by the user.",
    })
    with info_path.open("wb") as handle:
        plistlib.dump(info, handle, sort_keys=True)

    run(["xattr", "-cr", APP_PATH])
    run(["codesign", "--force", "--deep", "--sign", "-", APP_PATH])
    run(["codesign", "--verify", "--deep", "--strict", "--verbose=2", APP_PATH])


def verify_bundle_is_clean():
    forbidden_names = {"phlending.db", "phlending_demo.db", "profiles.json", "app.log"}
    found = [path for path in APP_PATH.rglob("*") if path.name.lower() in forbidden_names]
    if found:
        raise RuntimeError(f"Personal-data files found in bundle: {found}")


def create_dmg():
    shutil.rmtree(DMG_STAGE, ignore_errors=True)
    DMG_STAGE.mkdir(parents=True)
    shutil.copytree(APP_PATH, DMG_STAGE / APP_PATH.name, symlinks=True)
    os.symlink("/Applications", DMG_STAGE / "Applications")
    shutil.copy2(PROJECT_DIR / "packaging" / "README-DEMO.txt", DMG_STAGE)

    for path in (DMG_PATH, CHECKSUM_PATH):
        path.unlink(missing_ok=True)
    run([
        "hdiutil",
        "create",
        "-volname",
        APP_NAME,
        "-srcfolder",
        DMG_STAGE,
        "-ov",
        "-format",
        "UDZO",
        DMG_PATH,
    ])

    digest = hashlib.sha256(DMG_PATH.read_bytes()).hexdigest()
    CHECKSUM_PATH.write_text(f"{digest}  {DMG_PATH.name}\n", encoding="ascii")


def main():
    verify_host()
    build_app()
    verify_bundle_is_clean()
    create_dmg()
    print(f"Application: {APP_PATH}")
    print(f"DMG: {DMG_PATH}")
    print(f"SHA-256: {CHECKSUM_PATH}")


if __name__ == "__main__":
    main()
