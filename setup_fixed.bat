@echo off
chcp 65001 >nul
cls
echo ========================================
echo BLOG PLATFORM - FIXED SETUP
echo ========================================
echo.

:: 1. Sprawdź Python
where python >nul 2>&1
if errorlevel 1 (
    echo Using 'py' instead of 'python'...
    set PYCMD=py
) else (
    set PYCMD=python
)

%PYCMD% --version

:: 2. Wyczyść stare .venv jeśli istnieje
if exist ".venv" (
    echo Closing Python processes...
    taskkill /F /IM python.exe /T >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo Removing old .venv...
    rmdir /s /q .venv 2>nul
)

:: 3. Utwórz venv
echo Creating virtual environment...
%PYCMD% -m venv .venv

:: 4. Aktywuj i zainstaluj MINIMALNE wymagania
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install Flask Flask-SQLAlchemy Flask-CORS Flask-Bcrypt Flask-JWT-Extended --quiet

:: 5. Utwórz prosty plik migracji w jednej linii
echo Creating migration script...
echo import sys, os^>migrate_temp.py
echo sys.path.insert(0, os.getcwd())^>>migrate_temp.py
echo from app import create_app^>>migrate_temp.py
echo from database import db^>>migrate_temp.py
echo from models.user import User^>>migrate_temp.py
echo app = create_app()^>>migrate_temp.py
echo with app.app_context():^>>migrate_temp.py
echo     db.create_all()^>>migrate_temp.py
echo     print("Tables created")^>>migrate_temp.py
echo     if not User.find_by_username('admin'):^>>migrate_temp.py
echo         admin = User(username='admin', email='admin@blog.platform', password='Admin123!', role='ADMIN')^>>migrate_temp.py
echo         db.session.add(admin)^>>migrate_temp.py
echo         db.session.commit()^>>migrate_temp.py
echo         print("Admin created")^>>migrate_temp.py

:: 6. Uruchom migrację
echo Running migrations...
python migrate_temp.py

:: 7. Usuń tymczasowy plik
del migrate_temp.py

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo To run the app:
echo   1. run_fixed.bat
echo   2. Or: call .venv\Scripts\activate.bat ^& python app.py
echo.
echo App will be at: http://localhost:5000
echo.
pause