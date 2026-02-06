@echo off
chcp 65001 >nul
echo ========================================
echo BLOG PLATFORM - Windows Setup
echo ========================================
echo.

:: Sprawdź czy Python jest zainstalowany
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python nie jest zainstalowany!
    echo Pobierz z: https://www.python.org/downloads/
    pause
    exit /b 1
)

py --version
echo.

:: Utwórz wirtualne środowisko w folderze .venv
if not exist ".venv" (
    echo Tworzenie wirtualnego środowiska...
    py -m venv .venv
    if errorlevel 1 (
        echo ERROR: Nie można utworzyć wirtualnego środowiska
        echo Upewnij się, że Python jest poprawnie zainstalowany
        pause
        exit /b 1
    )
    echo ✓ Wirtualne środowisko utworzone w .venv
) else (
    echo ✓ Wirtualne środowisko .venv już istnieje
)

:: Aktywacja venv i instalacja zależności
echo.
echo Instalowanie zależności...
call .venv\Scripts\activate.bat

:: Aktualizacja pip
echo Aktualizacja pip...
python -m pip install --upgrade pip --quiet

:: Sprawdź czy requirements.txt istnieje
if not exist "requirements.txt" (
    echo ERROR: Brak pliku requirements.txt
    pause
    exit /b 1
)

:: Instalacja zależności
echo Instalacja pakietów...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Instalacja zależności nie powiodła się
    echo Sprawdź czy masz połączenie z internetem
    pause
    exit /b 1
)

echo ✓ Zależności zainstalowane pomyślnie

:: Utwórz .env jeśli nie istnieje
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo ✓ Plik .env utworzony z .env.example
        echo   Edytuj plik .env przed uruchomieniem!
    ) else (
        echo Tworzenie podstawowego pliku .env...
        (
            echo # Blog Platform - Configuration
            echo FLASK_APP=app.py
            echo FLASK_ENV=development
            echo SECRET_KEY=dev-secret-key-change-in-production
            echo DATABASE_URL=sqlite:///blog.db
            echo JWT_SECRET_KEY=jwt-secret-key-change-in-production
            echo JWT_ACCESS_TOKEN_EXPIRES=900
            echo JWT_REFRESH_TOKEN_EXPIRES=604800
            echo AUTO_MIGRATE=true
            echo LOG_LEVEL=INFO
        ) > .env
        echo ✓ Plik .env utworzony
    )
) else (
    echo ✓ Plik .env już istnieje
)

:: Uruchom migracje bazy danych
echo.
echo ========================================
echo KONFIGURACJA BAZY DANYCH
echo ========================================
echo.

:: Sprawdź czy baza SQLite istnieje
if exist "blog.db" (
    echo ✓ Baza danych SQLite już istnieje
    echo   Plik: blog.db
) else (
    echo Baza danych nie istnieje, tworzenie...
)

echo Uruchamianie migracji...
python -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import create_app
    from database import db
    from models.user import User
    
    app = create_app()
    with app.app_context():
        # Tworzenie wszystkich tabel
        db.create_all()
        print('✓ Tabele utworzone')
        
        # Dodaj domyślnego admina jeśli nie istnieje
        admin = User.find_by_username('admin')
        if not admin:
            admin_user = User(
                username='admin',
                email='admin@blog.platform',
                password='Admin123!',
                role='ADMIN'
            )
            db.session.add(admin_user)
            db.session.commit()
            print('✓ Domyślny admin utworzony')
        
        print('✓ Migracje zakończone pomyślnie')
except Exception as e:
    print(f'✗ Błąd migracji: {e}')
    print('Możesz spróbować uruchomić ręcznie: flask init-db')
"
if errorlevel 1 (
    echo ⚠ Wystąpił problem z migracjami
    echo Możesz spróbować później: flask init-db
)

echo.
echo ========================================
echo INSTALACJA ZAKOŃCZONA
echo ========================================
echo.
echo Dostępne komendy:
echo   run.bat           - Uruchom aplikację
echo   flask init-db     - Ręczna migracja bazy
echo   flask routes      - Pokaż dostępne endpointy
echo.
echo Aplikacja będzie dostępna pod:
echo   http://localhost:5000
echo.
echo Endpoints testowe:
echo   http://localhost:5000/hello
echo   http://localhost:5000/api/health
echo.
echo Admin login:
echo   Username: admin
echo   Password: Admin123!
echo.
pause