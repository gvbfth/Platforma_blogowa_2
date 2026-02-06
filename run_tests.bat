@echo off
chcp 65001 >nul
echo ========================================
echo URUCHAMIANIE TESTOW
echo ========================================
echo.

:: Aktywacja wirtualnego środowiska
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Wirtualne srodowisko (.venv) nie istnieje!
    echo Uruchom najpierw run_app.bat aby utworzyc srodowisko.
    pause
    exit /b 1
)

:: Sprawdź czy pytest jest zainstalowany
pip show pytest >nul 2>&1
if errorlevel 1 (
    echo Instalowanie pytest...
    pip install pytest pytest-flask
)

echo.
echo ========================================
echo URUCHAMIANIE WSZYSTKICH TESTOW
echo ========================================
echo.

:: Uruchom testy
pytest tests/ -v

echo.
echo ========================================
echo TESTOWANIE ZAKONCZONE
echo ========================================
echo.
pause