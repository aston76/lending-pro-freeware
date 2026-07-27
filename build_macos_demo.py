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
APP_NAME = "Lending Pro Freeware"
DMG_VOLUME_NAME = "Lending Pro Freeware Installer"
BUNDLE_ID = "com.phlending.pro.demo"
ARCHITECTURE = "arm64"
BUILD_DIR = PROJECT_DIR / "build" / "macos-demo"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "work"
SPEC_DIR = BUILD_DIR / "spec"
DMG_RW_PATH = BUILD_DIR / "installer-rw.dmg"
RELEASE_DIR = PROJECT_DIR / "release"
APP_PATH = DIST_DIR / f"{APP_NAME}.app"
DMG_PATH = RELEASE_DIR / f"Lending-Pro-Freeware-macOS-{ARCHITECTURE}.dmg"
CHECKSUM_PATH = Path(str(DMG_PATH) + ".sha256")


def run(command):
    print("+", " ".join(str(part) for part in command))
    subprocess.run([str(part) for part in command], check=True, cwd=PROJECT_DIR)


def attach_writable_dmg():
    """Attach the temporary DMG and return its device and mount point."""
    command = [
        "hdiutil", "attach", "-readwrite", "-noverify", "-noautoopen",
        "-plist", DMG_RW_PATH,
    ]
    print("+", " ".join(str(part) for part in command))
    result = subprocess.run(
        [str(part) for part in command],
        check=True,
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
    )
    info = plistlib.loads(result.stdout)
    for entity in info.get("system-entities", []):
        if entity.get("mount-point"):
            return entity["dev-entry"], Path(entity["mount-point"])
    raise RuntimeError("The temporary installer DMG did not mount.")


def configure_finder_layout():
    """Create the familiar drag-the-app-to-Applications installer window."""
    script = f'''
tell application "Finder"
    tell disk "{DMG_VOLUME_NAME}"
        open
        set installerWindow to container window
        set current view of installerWindow to icon view
        set toolbar visible of installerWindow to false
        set statusbar visible of installerWindow to false
        set bounds of installerWindow to {{120, 120, 820, 600}}
        set viewOptions to the icon view options of installerWindow
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 112
        set text size of viewOptions to 13
        set label position of viewOptions to bottom
        set background color of viewOptions to {{61680, 62450, 63736}}
        set position of item "{APP_NAME}.app" of installerWindow to {{180, 205}}
        set position of item "Applications" of installerWindow to {{520, 205}}
        set position of item "README-DEMO.txt" of installerWindow to {{350, 365}}
        close installerWindow
        open
        update without registering applications
        delay 2
    end tell
end tell
'''
    run(["osascript", "-e", script])


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
        "CFBundleShortVersionString": "1.5.0",
        "CFBundleVersion": "7",
        "LSMinimumSystemVersion": "12.0",
        "NSCameraUsageDescription": "Lending Pro Freeware uses the camera to capture client photos.",
        "NSPhotoLibraryUsageDescription": "Lending Pro Freeware imports files selected by the user.",
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
    for path in (DMG_RW_PATH, DMG_PATH, CHECKSUM_PATH):
        path.unlink(missing_ok=True)

    run([
        "hdiutil", "create", "-size", "500m", "-fs", "HFS+",
        "-volname", DMG_VOLUME_NAME, DMG_RW_PATH,
    ])

    device = None
    try:
        device, mount_point = attach_writable_dmg()
        shutil.copytree(APP_PATH, mount_point / APP_PATH.name, symlinks=True)
        os.symlink("/Applications", mount_point / "Applications")
        shutil.copy2(
            PROJECT_DIR / "packaging" / "README-DEMO.txt",
            mount_point / "README-DEMO.txt",
        )
        configure_finder_layout()
        run(["sync"])
    finally:
        if device:
            run(["hdiutil", "detach", device])

    run([
        "hdiutil", "convert", DMG_RW_PATH, "-format", "UDZO",
        "-imagekey", "zlib-level=9", "-o", DMG_PATH,
    ])
    DMG_RW_PATH.unlink(missing_ok=True)

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
