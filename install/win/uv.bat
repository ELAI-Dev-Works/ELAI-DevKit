@echo off
setlocal
cls

echo ========================================================
echo                   UV Installer Helper
echo ========================================================
echo.
echo [What is UV?]
echo uv is an extremely fast Python package installer and resolver,
echo written in Rust. It replaces pip, pip-tools, and virtualenv.
echo.
echo [Installation Details]
echo Method:  Windows Package Manager (Winget)
echo Command: winget install -e --id astral-sh.uv
echo.
echo ========================================================
echo.
echo Please select an installation method:
echo.
echo 1. Automatic (via Winget)
echo    - We will run the winget command for you.
echo    - Requires Windows 10 (1709+) or Windows 11.
echo.
echo 2. Manual
echo    - We will open the official website. You can verify and
echo      install it yourself.
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto :auto_install
if "%choice%"=="2" goto :manual_install
echo Invalid choice. Exiting.
goto :eof

:auto_install
echo.
echo [INFO] Requesting permission to install...
set /p confirm="Do you want to run the installation command now? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Installation cancelled by user.
    pause
    goto :eof
)

echo.
echo [INFO] Running Winget...
winget install -e --id astral-sh.uv

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed.
    echo         Make sure 'App Installer' is installed from Microsoft Store.
    pause
    goto :eof
)

echo.
echo [SUCCESS] Installation command finished.
echo.
echo NOTE: You might need to restart your terminal or computer
echo       for the 'uv' command to be recognized in your PATH.
pause
goto :eof

:manual_install
echo.
echo [INFO] Opening https://docs.astral.sh/uv/ ...
start https://docs.astral.sh/uv/
echo.
echo Please follow the instructions on the website to install uv.
pause
goto :eof