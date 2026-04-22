@echo off
setlocal
cls

echo ===============================================
echo     ELAI-DevKit Environment ^& Tools Checker
echo ===============================================
echo.

REM --- 1. Check for UV (Critical) ---
echo [1/4] Checking 'uv' package manager...
where uv >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 'uv' is not found in PATH.
    echo         Please install uv: https://github.com/astral-sh/uv
    echo.
    pause
    exit /b 1
)
echo    - UV found.

REM --- 2. Check for NodeJS (Optional/Recommended) ---
echo [2/4] Checking 'Node.js'...
node -v >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] 'node' is not found in PATH.
    echo           NodeJS mode in Project Launcher will not work.
) else (
    echo    - Node.js found.
)

REM --- 3. Check for NPM (Optional/Recommended) ---
echo [3/4] Checking 'npm'...
call npm -v >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] 'npm' is not found in PATH.
) else (
    echo    - npm found.
)

REM --- 4. Virtual Environment & Dependencies ---
echo [4/4] Ensuring virtual environment...
IF NOT EXIST .venv (
    echo    - .venv not found. Creating via uv...
    uv venv > nul
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo    - Syncing dependencies...
uv pip sync requirements.txt --quiet
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to sync dependencies.
    pause
    exit /b 2
)

echo.
echo --- Running Python diagnostics script...
echo.

REM Run the python script for a detailed check
.\.venv\Scripts\python.exe diagnostic\check_tools.py

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python diagnostics failed.
    pause
    exit /b 3
)

echo.
echo ===============================================
echo            Check finished successfully.
echo ===============================================
echo.
endlocal