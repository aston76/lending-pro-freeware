#!/usr/bin/env python3
"""
PH-Lending Pro — macOS App Launcher Creator
Crée un vrai .app macOS qui démarre tout en double-cliquant.
Rapide : pas besoin de PyInstaller.
"""
import os
import stat
import subprocess
import shutil

APP_NAME = "PH-Lending Pro"
# Chemin du projet (si lancé depuis le dossier du projet, on récupère automatiquement)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "bin", "python3")
ICNS_PATH = os.path.join(PROJECT_DIR, "icon.icns")

# On place le .app dans le dossier du projet (ou changez ici vers /Applications)
APP_DEST = os.path.join(PROJECT_DIR, f"{APP_NAME}.app")


def create_app():
    print(f"📦 Création de {APP_NAME}.app...")

    # 1. Structure du bundle
    macos_dir = os.path.join(APP_DEST, "Contents", "MacOS")
    resources_dir = os.path.join(APP_DEST, "Contents", "Resources")
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # 2. Script de lancement
    launcher_path = os.path.join(macos_dir, APP_NAME)
    python_bin = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python3"

    launcher_content = f"""#!/bin/bash
# PH-Lending Pro — Launcher
cd "{PROJECT_DIR}"

# Utilise le venv si dispo, sinon python3 système
if [ -f "{VENV_PYTHON}" ]; then
    PYTHON="{VENV_PYTHON}"
else
    PYTHON=$(which python3)
fi

# Lance l'application (redirige logs vers ~/Library/Logs/PH-Lending.log)
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR"
exec "$PYTHON" main.py >> "$LOG_DIR/PH-Lending.log" 2>&1
"""
    with open(launcher_path, "w") as f:
        f.write(launcher_content)

    # Rendre exécutable
    os.chmod(launcher_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    # 3. Info.plist
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
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSCameraUsageDescription</key>
    <string>PH-Lending Pro needs camera access to capture client photos.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>PH-Lending Pro needs microphone access for video calls.</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>PH-Lending Pro needs photo library access to import documents.</string>
</dict>
</plist>
"""
    with open(plist_path, "w") as f:
        f.write(plist_content)

    # 4. Copie l'icône
    if os.path.exists(ICNS_PATH):
        dest_icns = os.path.join(resources_dir, "icon.icns")
        shutil.copy2(ICNS_PATH, dest_icns)
        print(f"🎨 Icône copiée")
    else:
        print("⚠️  icon.icns non trouvé — l'app utilisera une icône générique")
        print("   Lancez d'abord: python3 generate_icon.py")

    # 5. Forcer macOS à reconnaître le bundle
    subprocess.run(["touch", APP_DEST], check=False)
    subprocess.run(["xattr", "-cr", APP_DEST], check=False)

    print(f"\n✅ Terminé !")
    print(f"📁 App créée : {APP_DEST}")
    print(f"\n👉 Double-cliquez sur \"{APP_NAME}.app\" pour lancer l'application")
    print(f"   Ou copiez-la dans /Applications/ pour un accès permanent :\n")
    print(f'   cp -r "{APP_DEST}" /Applications/')

    # Ouvrir le dossier dans Finder
    subprocess.run(["open", PROJECT_DIR], check=False)


if __name__ == "__main__":
    create_app()
