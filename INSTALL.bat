@echo off
setlocal enabledelayedexpansion
title Lending Pro Freeware — Installation
color 0A

echo.
echo  ==========================================================
echo    Lending Pro Freeware  ^|  Installation automatique Windows
echo  ==========================================================
echo.
echo  Ce programme va installer Lending Pro Freeware sur votre ordinateur.
echo  L'operation peut prendre entre 5 et 10 minutes.
echo  Merci de ne PAS fermer cette fenetre.
echo.
echo  Appuyez sur une touche pour commencer...
pause >nul

:: ──────────────────────────────────────────────────────
:: ETAPE 1 — Verifier / Installer Python
:: ──────────────────────────────────────────────────────
echo.
echo  [1/5] Verification de Python...
echo  ──────────────────────────────────────────────────────

python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo        OK : %%v detecte.
    goto :python_ok
)

:: Python introuvable → telechargement automatique
echo        Python non detecte. Telechargement en cours...
echo        ^(Connexion Internet requise^)
echo.

powershell -NoProfile -Command ^
    "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_setup.exe' -UseBasicParsing" 2>nul

if not exist "%TEMP%\python_setup.exe" (
    echo.
    echo  [ERREUR] Telechargement de Python impossible.
    echo           Verifiez votre connexion Internet, puis reessayez.
    echo.
    pause
    exit /b 1
)

echo        Installation de Python 3.11 ^(patientez...^)
"%TEMP%\python_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0 Include_test=0
del /q "%TEMP%\python_setup.exe" 2>nul

:: Ajouter Python au PATH de la session courante
set "PY_HOME=%LOCALAPPDATA%\Programs\Python\Python311"
set "PATH=%PY_HOME%;%PY_HOME%\Scripts;%PATH%"

:: Verifier que Python fonctionne maintenant
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERREUR] L'installation Python a echoue.
    echo           Redemarrez votre PC puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)
echo        Python installe avec succes !

:python_ok

:: ──────────────────────────────────────────────────────
:: ETAPE 2 — Environnement virtuel
:: ──────────────────────────────────────────────────────
echo.
echo  [2/5] Preparation de l'environnement de compilation...
echo  ──────────────────────────────────────────────────────

:: Supprimer un eventuel venv precedent
if exist "venv_win" (
    echo        Nettoyage de l'ancien environnement...
    rmdir /s /q "venv_win"
)

python -m venv venv_win >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Impossible de creer l'environnement virtuel.
    pause
    exit /b 1
)

call venv_win\Scripts\activate.bat
echo        Environnement pret.

:: ──────────────────────────────────────────────────────
:: ETAPE 3 — Installation des bibliotheques
:: ──────────────────────────────────────────────────────
echo.
echo  [3/5] Installation des bibliotheques Python...
echo        ^(2 a 4 minutes — patientez...^)
echo  ──────────────────────────────────────────────────────

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

if errorlevel 1 (
    echo.
    echo  [ERREUR] Installation des bibliotheques echouee.
    echo           Verifiez votre connexion Internet, puis reessayez.
    echo.
    pause
    exit /b 1
)
echo        Toutes les bibliotheques sont installes.

:: ──────────────────────────────────────────────────────
:: ETAPE 4 — Compilation de l'application
:: ──────────────────────────────────────────────────────
echo.
echo  [4/5] Compilation de l'application...
echo        ^(1 a 2 minutes — patientez...^)
echo  ──────────────────────────────────────────────────────

:: Tentative de conversion de l'icone Mac (.icns) en Windows (.ico)
if exist "icon.icns" (
    python -c "from PIL import Image; img = Image.open('icon.icns'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])" 2>nul
)

:: Nettoyage des anciens builds
if exist "build" rmdir /s /q "build"
if exist "dist\Lending Pro Freeware" rmdir /s /q "dist\Lending Pro Freeware"
if exist "Lending Pro Freeware.spec" del /q "Lending Pro Freeware.spec"

:: Commande PyInstaller (avec ou sans icone)
set "ICON_PARAM="
if exist "icon.ico" set "ICON_PARAM=--icon icon.ico"

pyinstaller ^
    --name "Lending Pro Freeware" ^
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
    --hidden-import "json" ^
    --collect-all "webview" ^
    --collect-all "cv2" ^
    --collect-all "dateutil" ^
    main.py

if errorlevel 1 (
    echo.
    echo  [ERREUR] La compilation a echoue.
    echo           Lisez les messages d'erreur ci-dessus.
    echo.
    pause
    exit /b 1
)

if not exist "dist\Lending Pro Freeware\Lending Pro Freeware.exe" (
    echo.
    echo  [ERREUR] Le fichier .exe est introuvable apres compilation.
    pause
    exit /b 1
)

echo        Application compilee avec succes !

:: ──────────────────────────────────────────────────────
:: ETAPE 5 — Raccourci sur le Bureau
:: ──────────────────────────────────────────────────────
echo.
echo  [5/5] Creation du raccourci sur le Bureau...
echo  ──────────────────────────────────────────────────────

set "EXE_PATH=%~dp0dist\Lending Pro Freeware\Lending Pro Freeware.exe"
set "WORK_DIR=%~dp0dist\Lending Pro Freeware"
set "SHORTCUT=%USERPROFILE%\Desktop\Lending Pro Freeware.lnk"
set "ICO=%~dp0icon.ico"

powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%WORK_DIR%'; if (Test-Path '%ICO%') { $s.IconLocation = '%ICO%' }; $s.Save()"

if exist "%SHORTCUT%" (
    echo        Raccourci cree sur le Bureau.
) else (
    echo        ^(Raccourci non cree — lancez l'app depuis dist\Lending Pro Freeware\^)
)

:: ──────────────────────────────────────────────────────
:: NETTOYAGE
:: ──────────────────────────────────────────────────────
echo.
echo  Nettoyage des fichiers temporaires...
if exist "venv_win" rmdir /s /q "venv_win"
if exist "build" rmdir /s /q "build"
if exist "Lending Pro Freeware.spec" del /q "Lending Pro Freeware.spec"

:: ──────────────────────────────────────────────────────
:: SUCCES
:: ──────────────────────────────────────────────────────
echo.
echo  ==========================================================
echo    Installation terminee avec succes !
echo  ==========================================================
echo.
echo    Un raccourci "Lending Pro Freeware" a ete cree sur
echo    votre Bureau. Double-cliquez dessus pour lancer
echo    l'application.
echo.
echo    IMPORTANT : Ne deplacez pas ni ne supprimez le
echo    dossier dans lequel vous avez extrait ce ZIP,
echo    sinon le raccourci ne fonctionnera plus.
echo.
pause
