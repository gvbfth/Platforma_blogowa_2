@echo off
chcp 65001 >nul
cls
echo ========================================
echo URUCHAMIANIE BLOG PLATFORM
echo ========================================
echo.

:: Sprawdzanie czy venv istnieje
if not exist ".venv" (
    echo ERROR: Brak .venv!
    echo Uruchom setup_final.bat
    pause
    exit /b 1
)

:: Sprawdzanie czy baza istnieje
if not exist "blog.db" (
    echo ⚠ Baza danych nie istnieje!
    echo Tworzenie bazy...
    python -c "
import sys
sys.path.insert(0, '.')
from app import create_app
from database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✓ Baza utworzona')
"
)

:: Aktywuj venv i uruchom
call .venv\Scripts\activate.bat

echo.
echo ========================================
echo APLIKACJA URUCHAMIANA
echo ========================================
echo.
echo URL: http://localhost:5000
echo Naciśnij Ctrl+C aby zatrzymać
echo ========================================
echo.

python app.py

pause