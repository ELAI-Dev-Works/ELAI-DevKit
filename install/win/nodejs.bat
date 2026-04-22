@echo off
setlocal
cls

echo ========================================================
echo                 Node.js Installer Helper
echo ========================================================
echo.
echo [What is Node.js?]
echo Node.js is a free, open-source, cross-platform JavaScript runtime environment
echo that executes JavaScript code outside a web browser.
echo It is required for Web/NodeJS project modes.
echo.
echo [Installation Details via Winget]
echo Method:  Windows Package Manager (Winget)
echo Command: winget install -e --id OpenJS.NodeJS
echo.
echo ========================================================
echo.
echo Please select an installation method:
echo.
echo 1. Automatic (via Winget)
echo    - We will run the winget command for you.
echo    - This installs the official Node.js (LTS) package.
echo.
echo 2. Manual
echo    - We will open the official Node.js website.
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto :auto_install
if "%choice%"=="2" goto :manual_install
echo Invalid choice. Exiting.
goto :eof

:auto_install
echo.
echo [INFO] Requesting permission to install Node.js...
set /p confirm="Do you want to run the installation command now? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Installation cancelled by user.
    pause
    goto :eof
)

echo.
echo [INFO] Running Winget...
winget install -e --id OpenJS.NodeJS

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
echo       for the 'node' and 'npm' commands to be recognized.
pause
goto :eof

:manual_install
echo.
echo [INFO] Opening https://nodejs.org/ ...
start https://nodejs.org/
echo.
echo Please download and install Node.js (LTS recommended) from the website.
echo IMPORTANT: Ensure "Add to PATH" is selected during installation.
pause
goto :eof