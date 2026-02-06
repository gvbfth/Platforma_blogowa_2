@echo off
chcp 65001 >nul
cls
echo ========================================
echo RUNNING BLOG PLATFORM
echo ========================================
echo.

if not exist ".venv" (
    echo ERROR: No .venv found!
    echo Run setup_fixed.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo App starting at: http://localhost:5000
echo Press Ctrl+C to stop
echo.
python app.py