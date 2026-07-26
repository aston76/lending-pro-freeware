#!/bin/bash
# ============================================================
#  create_windows_zip.sh
#  Lance depuis le Mac — crée le ZIP Windows de Lending Pro Freeware
#  Usage : bash create_windows_zip.sh
# ============================================================

set -e
cd "$(dirname "$0")"

APP_NAME="Lending-Pro-Freeware-Windows"
ZIP_FILE="${APP_NAME}.zip"

echo ""
echo "  ======================================================"
echo "   Lending Pro Freeware — Création du paquet Windows"
echo "  ======================================================"
echo ""

# Supprimer un ancien ZIP s'il existe
if [ -f "$ZIP_FILE" ]; then
    echo "  🗑  Ancien paquet supprimé : $ZIP_FILE"
    rm -f "$ZIP_FILE"
fi

echo "  📦  Création du ZIP en cours..."
echo ""

# Créer le ZIP avec uniquement les fichiers nécessaires
zip -r "$ZIP_FILE" \
    "main.py" \
    "app_config.py" \
    "installation_id.py" \
    "currency_utils.py" \
    "api.py" \
    "database.py" \
    "loan_engine.py" \
    "backup.py" \
    "logger.py" \
    "pdf_generator.py" \
    "excel_export.py" \
    "demo_generator.py" \
    "generate_icon.py" \
    "requirements.txt" \
    "INSTALL.bat" \
    "README_WINDOWS.txt" \
    "LICENSE" \
    "web/" \
    -x "web/.DS_Store" \
    -x "**/.DS_Store" \
    -x "**/__pycache__/*" \
    -x "*.pyc" \
    2>/dev/null

# Ajouter l'icone si elle existe
if [ -f "icon.icns" ]; then
    zip -u "$ZIP_FILE" "icon.icns" 2>/dev/null
    echo "  🎨  Icône incluse."
fi

echo ""
echo "  ======================================================"
echo "   ✅  Paquet créé avec succès !"
echo "  ======================================================"
echo ""
echo "   Fichier : $(pwd)/$ZIP_FILE"
SIZE=$(du -sh "$ZIP_FILE" | cut -f1)
echo "   Taille  : $SIZE"
echo ""
echo "   Envoyez ce fichier ZIP à votre ami/client Windows."
echo "   Il devra :"
echo "     1. Extraire le ZIP dans un dossier permanent"
echo "     2. Double-cliquer sur INSTALL.bat"
echo "     3. Attendre 5-10 min (installation automatique)"
echo ""
