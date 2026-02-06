@echo off
chcp 65001 >nul
echo ========================================
echo URUCHAMIANIE BLOG PLATFORM
echo ========================================
echo.

:: Sprawdzanie czy venv istnieje
if not exist ".venv" (
    echo Tworzenie wirtualnego środowiska...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Instalowanie pakietów...
    pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-CORS Flask-Bcrypt Flask-JWT-Extended Flask-Limiter python-dotenv PyJWT structlog email-validator
) else (
    call .venv\Scripts\activate.bat
)

:: Sprawdzanie czy baza istnieje
if not exist "blog.db" (
    echo Tworzenie bazy danych...
    python init.py
)

echo.
echo ========================================
echo APLIKACJA URUCHAMIANA
echo ========================================
echo.
echo Adres: http://localhost:5000
echo.
echo Endpointy:
echo   /hello          - Strona powitalna
echo   /api/health     - Status aplikacji
echo   /api/auth/register - Rejestracja
echo.
echo Naciśnij Ctrl+C aby zatrzymać
echo ========================================
echo.

python app.py

pause