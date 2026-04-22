@echo off
setlocal
cls

echo ========================================================
echo                 Python Installer Helper
echo ========================================================
echo.
echo [What is Python?]
echo Python is a high-level, general-purpose programming language.
echo It is required to run ELAI-DevKit and many other tools.
echo.
echo [Installation Details via Winget]
echo Method:  Windows Package Manager (Winget)
echo Command: winget install -e --id Python.Python.^<version^>
echo.
echo ========================================================
echo.
echo Please select an installation method:
echo.
echo 1. Automatic (via Winget)
echo    - You can choose the version (e.g. 3.11, 3.12).
echo    - We will download and install the official Python package.
echo.
echo 2. Manual
echo    - We will open the official Python website.
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto :auto_install
if "%choice%"=="2" goto :manual_install
echo Invalid choice. Exiting.
goto :eof

:auto_install
echo.
echo Enter the version you want to install.
echo Common versions: 3.10, 3.11, 3.12, 3.13
echo.
set /p py_ver="Version to install (e.g. 3.11): "

if "%py_ver%"=="" (
    echo No version specified. Aborting.
    pause
    goto :eof
)

echo.
echo [INFO] Requesting permission to install Python %py_ver%...
set /p confirm="Do you want to proceed? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Installation cancelled by user.
    pause
    goto :eof
)

echo.
echo [INFO] Installing Python.Python.%py_ver%...
echo Command: winget install -e --id Python.Python.%py_ver%
winget install -e --id Python.Python.%py_ver%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed.
    echo         Please check the version number or your internet connection.
    pause
    goto :eof
)

echo.
echo [SUCCESS] Installation command finished.
echo.
echo NOTE: You might need to restart your terminal or computer
echo       for the 'python' command to be recognized.
pause
goto :eof

:manual_install
echo.
echo [INFO] Opening https://www.python.org/downloads/ ...
start https://www.python.org/downloads/
echo.
echo Please download and install Python from the website.
echo IMPORTANT: Check "Add Python to PATH" during installation.
pause
goto :eof