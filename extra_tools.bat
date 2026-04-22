@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
cls

echo ===========================================
echo             Extra Tools Menu
echo ===========================================
echo.

IF NOT EXIST .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

set idx=1
for /r extra_tools %%F in (*.py) do (
    set "script[!idx!]=%%F"
    rem Get relative path for display
    set "display_path=%%F"
    set "display_path=!display_path:%cd%\extra_tools\=!"
    echo [!idx!] !display_path!
    set /a idx+=1
)

set /a max_idx=idx-1
if %max_idx%==0 (
    echo No scripts found in the extra_tools folder.
    pause
    exit /b 0
)

echo.
set /p choice="Select a script to run (1-%max_idx%): "

if defined script[%choice%] (
    set selected=!script[%choice%]!
    echo.
    echo Running !selected!...
    echo.
    .\.venv\Scripts\python.exe "!selected!"
) else (
    echo Invalid choice.
)

echo.
pause