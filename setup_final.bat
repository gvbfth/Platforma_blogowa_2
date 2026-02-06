@echo off
chcp 65001 >nul
cls
echo ========================================
echo BLOG PLATFORM - FINAL SETUP
echo ========================================
echo.

:: 1. Sprawdź Python
py --version
if errorlevel 1 (
    echo ERROR: Python nie znaleziony!
    pause
    exit /b 1
)

:: 2. Usuń stary .venv
if exist ".venv" (
    echo Usuwanie starego .venv...
    taskkill /F /IM python.exe /T >nul 2>&1
    timeout /t 2 /nobreak >nul
    rmdir /s /q .venv 2>nul
)

:: 3. Utwórz venv
echo Tworzenie wirtualnego środowiska...
py -m venv .venv
if errorlevel 1 (
    echo ERROR: Nie można utworzyć venv!
    pause
    exit /b 1
)

echo ✓ .venv utworzony

:: 4. Zainstaluj wszystkie wymagane pakiety
echo Instalowanie wszystkich wymaganych pakietów...
call .venv\Scripts\activate.bat

:: Utwórz kompletny requirements.txt
if not exist "requirements.txt" (
    echo Tworzenie requirements.txt...
    (
        echo Flask==3.0.0
        echo Flask-SQLAlchemy==3.1.1
        echo Flask-Migrate==4.0.5
        echo Flask-CORS==4.0.0
        echo Flask-Bcrypt==1.0.1
        echo Flask-JWT-Extended==4.6.0
        echo python-dotenv==1.0.0
        echo PyJWT==2.8.0
        echo structlog==24.1.0
        echo email-validator==2.1.1
    ) > requirements.txt
)

pip install -r requirements.txt --quiet

echo ✓ Wszystkie pakiety zainstalowane

:: 5. Utwórz .env jeśli nie istnieje
if not exist ".env" (
    echo Tworzenie pliku .env...
    (
        echo FLASK_APP=app.py
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo DATABASE_URL=sqlite:///blog.db
        echo JWT_SECRET_KEY=jwt-secret-key-change-in-production
        echo JWT_ACCESS_TOKEN_EXPIRES=900
        echo JWT_REFRESH_TOKEN_EXPIRES=604800
    ) > .env
    echo ✓ .env utworzony
)

:: 6. Utwórz skrypt migracji
echo Tworzenie skryptu migracji...
(
    echo import sys
    echo import os
    echo sys.path.insert(0, os.getcwd())
    echo from app import create_app
    echo from database import db
    echo from models.user import User
    echo.
    echo print("Uruchamianie migracji bazy danych...")
    echo app = create_app()
    echo with app.app_context():
    echo     db.create_all()
    echo     print("✓ Tabele utworzone")
    echo.
    echo     admin = User.find_by_username('admin')
    echo     if not admin:
    echo         print("Tworzenie użytkownika admin...")
    echo         admin_user = User(
    echo             username='admin',
    echo             email='admin@blog.platform',
    echo             password='Admin123!',
    echo             role='ADMIN'
    echo         )
    echo         db.session.add(admin_user)
    echo         db.session.commit()
    echo         print("✓ Admin utworzony")
    echo.
    echo print("✓ Migracje zakończone pomyślnie!")
) > migrate.py

:: 7. Uruchom migracje
echo Uruchamianie migracji...
python migrate.py

:: 8. Usuń tymczasowy plik
del migrate.py

echo.
echo ========================================
echo INSTALACJA ZAKOŃCZONA!
echo ========================================
echo.
echo Aby uruchomić aplikację:
echo   run_final.bat   lub   python app.py
echo.
echo Aplikacja będzie dostępna pod:
echo   http://localhost:5000
echo.
echo Domyślny użytkownik admin:
echo   Username: admin
echo   Password: Admin123!
echo.
pause