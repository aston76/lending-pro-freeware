#!/bin/bash
# PH-Lending Pro — macOS Build Script
# Generates a double-clickable .app bundle using PyInstaller
# Usage: bash setup_pyinstaller.sh

set -e
cd "$(dirname "$0")"

echo "🚀 Building PH-Lending Pro for macOS..."
echo ""

# 1. Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# 2. Generate app icon
echo "🎨 Generating app icon..."
python3 generate_icon.py || echo "⚠️  Icon generation skipped (Pillow may need install)"

# 3. Clean previous builds
echo "🧹 Cleaning old builds..."
rm -rf build dist "PH-Lending Pro.spec"

# 4. Run PyInstaller
echo "🔨 Building .app bundle..."
pyinstaller \
    --name "PH-Lending Pro" \
    --windowed \
    --onedir \
    $([ -f icon.icns ] && echo "--icon icon.icns") \
    --add-data "web:web" \
    --osx-bundle-identifier com.phlending.pro \
    --hidden-import "webview" \
    --hidden-import "webview.platforms.cocoa" \
    --hidden-import "openpyxl" \
    --hidden-import "openpyxl.styles" \
    --hidden-import "openpyxl.utils" \
    --hidden-import "reportlab" \
    --hidden-import "reportlab.pdfgen" \
    --hidden-import "reportlab.lib" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    --hidden-import "google.auth" \
    --hidden-import "googleapiclient" \
    --hidden-import "dateutil" \
    --hidden-import "dateutil.relativedelta" \
    --collect-all "webview" \
    main.py

# 5. Add permissions to Info.plist
PLIST="dist/PH-Lending Pro.app/Contents/Info.plist"
if [ -f "$PLIST" ]; then
    echo "📋 Adding macOS permissions..."
    /usr/libexec/PlistBuddy -c "Add :NSCameraUsageDescription string 'PH-Lending Pro needs camera access to capture client photos'" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :NSPhotoLibraryUsageDescription string 'PH-Lending Pro needs photo library access to import documents'" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :NSDesktopFolderUsageDescription string 'PH-Lending Pro needs folder access to save backups'" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :NSDocumentsFolderUsageDescription string 'PH-Lending Pro needs Documents access to save exports'" "$PLIST" 2>/dev/null || true
fi

# 6. Copy to Applications (optional prompt)
APP_PATH="dist/PH-Lending Pro.app"
echo ""
echo "✅ Build complete!"
echo "📦 App: $(pwd)/$APP_PATH"
echo ""
echo "To launch: open '$APP_PATH'"
echo ""
echo "To install in Applications folder:"
echo "  cp -r '$APP_PATH' /Applications/"
