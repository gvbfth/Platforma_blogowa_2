@echo off
chcp 65001 >nul
echo ========================================
echo URUCHAMIANIE BLOG PLATFORM
echo ========================================
echo.

:: Sprawdź czy .venv istnieje
if not exist ".venv" (
    echo ERROR: Brak wirtualnego środowiska!
    echo Uruchom najpierw setup.bat
    pause
    exit /b 1
)

:: Aktywuj venv
call .venv\Scripts\activate.bat

:: Sprawdź czy baza istnieje
if not exist "blog.db" (
    echo ⚠ Baza danych nie istnieje
    echo Tworzenie bazy danych...
    python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import create_app
    from database import db
    app = create_app()
    with app.app_context():
        db.create_all()
        print('✓ Baza danych utworzona')
except Exception as e:
    print(f'✗ Błąd: {e}')
"
)

:: Uruchom aplikację
echo.
echo ========================================
echo APLIKACJA URUCHAMIANA
echo ========================================
echo.
echo URL: http://localhost:5000
echo.
echo Endpoints:
echo   /hello          - Strona powitalna
echo   /api/health     - Status aplikacji
echo   /api/auth/register - Rejestracja
echo.
echo Naciśnij Ctrl+C aby zatrzymać
echo ========================================
echo.
python app.py

pause