@echo off
setlocal
cd /d "%~dp0"
cls

echo ============================================
echo            ELAI-DevKit Diagnostics
echo ============================================
echo.

IF NOT EXIST .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

.\.venv\Scripts\python.exe -m systems.diagnostic
pause