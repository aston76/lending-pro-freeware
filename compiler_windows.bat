@echo off
title Compilation Windows - PH-Lending Pro
color 0B
echo.
echo  ==========================================
echo    Compilation .exe — PH-Lending Pro
echo    (Usage developpeur)
echo  ==========================================
echo.

:: Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou absent du PATH.
    pause
    exit /b
)

:: Creer venv si absent
if not exist "venv_win" (
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv venv_win
)

:: Activer et installer
echo [2/4] Installation des dependances...
call venv_win\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

:: Convertir l'icone si possible
if exist "icon.icns" (
    python -c "from PIL import Image; img = Image.open('icon.icns'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])" 2>nul
)

:: Nettoyage
echo [3/4] Nettoyage des anciens builds...
if exist "build" rmdir /s /q "build"
if exist "dist\PH-Lending Pro" rmdir /s /q "dist\PH-Lending Pro"
if exist "PH-Lending Pro.spec" del /q "PH-Lending Pro.spec"

:: Compiler
echo [4/4] Compilation PyInstaller (1-2 minutes)...

set "ICON_PARAM="
if exist "icon.ico" set "ICON_PARAM=--icon icon.ico"

pyinstaller ^
    --name "PH-Lending Pro" ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    %ICON_PARAM% ^
    --add-data "web;web" ^
    --hidden-import "webview" ^
    --hidden-import "webview.platforms.winforms" ^
    --hidden-import "webview.platforms.edgechromium" ^
    --hidden-import "openpyxl" ^
    --hidden-import "openpyxl.styles" ^
    --hidden-import "openpyxl.utils" ^
    --hidden-import "openpyxl.cell" ^
    --hidden-import "reportlab" ^
    --hidden-import "reportlab.pdfgen" ^
    --hidden-import "reportlab.pdfgen.canvas" ^
    --hidden-import "reportlab.lib" ^
    --hidden-import "reportlab.lib.pagesizes" ^
    --hidden-import "reportlab.lib.units" ^
    --hidden-import "reportlab.lib.colors" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageDraw" ^
    --hidden-import "PIL.ImageFont" ^
    --hidden-import "google.auth" ^
    --hidden-import "google.auth.transport.requests" ^
    --hidden-import "googleapiclient" ^
    --hidden-import "googleapiclient.discovery" ^
    --hidden-import "google_auth_oauthlib" ^
    --hidden-import "google_auth_oauthlib.flow" ^
    --hidden-import "dateutil" ^
    --hidden-import "dateutil.relativedelta" ^
    --hidden-import "cv2" ^
    --hidden-import "sqlite3" ^
    --collect-all "webview" ^
    --collect-all "cv2" ^
    --collect-all "dateutil" ^
    main.py

echo.
echo  ==========================================
if exist "dist\PH-Lending Pro\PH-Lending Pro.exe" (
    echo    Compilation reussie !
    echo    EXE : dist\PH-Lending Pro\PH-Lending Pro.exe
) else (
    echo    [ERREUR] Compilation echouee.
)
echo  ==========================================
echo.
pause
