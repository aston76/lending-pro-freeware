@echo off
title PH-Lending Pro
echo ==========================================
echo       Lancement de PH-Lending Pro...
echo ==========================================
echo.

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    echo.
    echo Veuillez installer Python depuis le Microsoft Store :
    echo https://apps.microsoft.com/detail/9pjpw5ldxlz5
    echo.
    echo Ou depuis le site officiel : https://www.python.org/downloads/
    echo (IMPORTANT : Cochez "Add python.exe to PATH" lors de l'installation)
    echo.
    pause
    exit /b
)

:: Créer l'environnement virtuel s'il n'existe pas
if not exist "venv_win" (
    echo [1/3] Creation de l'environnement temp (venv_win)...
    python -m venv venv_win
)

:: Activer l'environnement et installer les dépendances
echo [2/3] Verification des dependances (patientez un instant)...
call venv_win\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Lancer l'application
echo [3/3] Demarrage de l'application...
python main.py

pause
