@echo off
setlocal
cd /d "%~dp0"
cls

echo ============================================
echo                  ELAI-DevKit
echo ============================================
echo.
REM --- Run Launcher ---
echo [2/2] Handing over to Python Launcher...
echo.

python launch.py %*
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Launcher exited with error code %ERRORLEVEL%.
    pause
)