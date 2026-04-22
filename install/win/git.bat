@echo off
setlocal
cls

echo ========================================================
echo                   Git Installer Helper
echo ========================================================
echo.
echo [What is Git?]
echo Git is a free and open source distributed version control system
echo designed to handle everything from small to very large projects
echo with speed and efficiency.
echo.
echo [Installation Details via Winget]
echo Method:  Windows Package Manager (Winget)
echo Command: winget install -e --id Git.Git
echo.
echo ========================================================
echo.
echo Please select an installation method:
echo.
echo 1. Automatic (via Winget)
echo    - We will run the winget command for you.
echo    - This installs the official Git for Windows package.
echo.
echo 2. Manual
echo    - We will open the official Git website.
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto :auto_install
if "%choice%"=="2" goto :manual_install
echo Invalid choice. Exiting.
goto :eof

:auto_install
echo.
echo [INFO] Requesting permission to install Git...
set /p confirm="Do you want to run the installation command now? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Installation cancelled by user.
    pause
    goto :eof
)

echo.
echo [INFO] Running Winget...
winget install -e --id Git.Git

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
echo       for the 'git' command to be recognized in your PATH.
pause
goto :eof

:manual_install
echo.
echo [INFO] Opening https://git-scm.com/downloads ...
start https://git-scm.com/downloads
echo.
echo Please download and install Git from the website.
echo IMPORTANT: Select "Add Git to PATH" if asked during installation.
pause
goto :eof