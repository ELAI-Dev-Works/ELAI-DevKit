from typing import Tuple

def parse(args_list: list) -> bool:
    if '-python' in args_list:
        return True
    return False

def run(fs, launch_file: str, dependencies: list, project_name: str, platforms: set) -> Tuple[bool, str]:
    try:
        # 1. Create dependency files
        req_in_content = "\n".join(dependencies)
        fs.write("@ROOT/requirements.in", req_in_content)

        files_created = []

        if 'win' in platforms:
            # Create 'setup_run(uv).bat'
            uv_bat_content = get_uv_run_bat_template().format(launch_file=launch_file, project_name=project_name)
            fs.write("@ROOT/setup_run(uv).bat", uv_bat_content)

            # Create 'run(pip).bat'
            pip_bat_content = get_pip_run_bat_template().format(launch_file=launch_file, project_name=project_name)
            fs.write("@ROOT/run(pip).bat", pip_bat_content)
            files_created.append("Windows (.bat)")

        if 'unix' in platforms:
            # Create 'setup_run(uv).sh'
            uv_sh_content = get_uv_run_sh_template().format(launch_file=launch_file, project_name=project_name)
            # Use explicit \n to avoid CRLF issues on Windows hosts
            fs.write_bytes("@ROOT/setup_run(uv).sh", uv_sh_content.replace('\r\n', '\n').encode('utf-8'))

            # Create 'run(pip).sh'
            pip_sh_content = get_pip_run_sh_template().format(launch_file=launch_file, project_name=project_name)
            fs.write_bytes("@ROOT/run(pip).sh", pip_sh_content.replace('\r\n', '\n').encode('utf-8'))
            files_created.append("Unix (.sh)")

        return True, f"Python environment files created for: {', '.join(files_created)}."
    except Exception as e:
        return False, f"Error creating python files: {e}"

def get_uv_run_bat_template():
    return """@echo off
setlocal
cls

echo ============================================
echo      {project_name} (Setup ^& Run - UV)
echo ============================================
echo.
echo [INFO] This script uses 'uv' for fast setup and dependency compilation.
echo.

REM --- STAGE 1: Prepare Environment ---
call :prepare_env
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Environment preparation failed. Exiting.
    pause
    exit /b 1
)

REM --- STAGE 2: Run Application ---
echo.
echo --- Starting Application ---
.\\.venv\\Scripts\\python.exe {launch_file}

echo.
echo --- Application exited. Press any key to close. ---
pause
goto :eof

REM =================================================================
REM |            Environment Preparation Function                   |
REM =================================================================
:prepare_env
    echo [1/2] Verifying virtual environment...
    IF NOT EXIST .venv (
        echo    - Not found. Creating now...
        uv venv > nul
        IF %ERRORLEVEL% NEQ 0 exit /b 1
    )

    echo [2/2] Compiling and Syncing Dependencies...
    set "COMPILE_NEEDED="
    IF NOT EXIST requirements.txt SET "COMPILE_NEEDED=true"
    IF EXIST requirements.txt (
        for %%F in (requirements.in) do for %%G in (requirements.txt) do if "%%~tF" gtr "%%~tG" SET "COMPILE_NEEDED=true"
    )

    IF DEFINED COMPILE_NEEDED (
        echo    - Compiling 'requirements.txt' from 'requirements.in'...
        uv pip compile requirements.in -o requirements.txt > nul
        IF %ERRORLEVEL% NEQ 0 exit /b 2
    )

    uv pip sync requirements.txt --quiet
    IF %ERRORLEVEL% NEQ 0 exit /b 3
    echo    - Dependencies are in sync.
goto :eof
"""

def get_pip_run_bat_template():
    return """@echo off
setlocal
cls

echo ============================================
echo      {project_name} (Run - Pip/Standard)
echo ============================================
echo.
echo [INFO] This script uses standard 'pip' and 'requirements.txt(need created)'.
echo        Use this for offline runs or if 'uv' is not available.
echo.

REM --- STAGE 1: Prepare Environment ---
call :prepare_env
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Environment preparation failed. Exiting.
    pause
    exit /b 1
)

REM --- STAGE 2: Run Application ---
echo.
echo --- Starting Application ---
.\\.venv\\Scripts\\python.exe {launch_file}

echo.
echo --- Application exited. Press any key to close. ---
pause
goto :eof

REM =================================================================
REM |            Environment Preparation Function                   |
REM =================================================================
:prepare_env
    echo [1/2] Verifying virtual environment...
    IF NOT EXIST .venv (
        echo    - Not found. Creating now...
        python -m venv .venv
        IF %ERRORLEVEL% NEQ 0 exit /b 1
    )

    echo [2/2] Installing Dependencies...
    pip install -r requirements.txt --quiet
    IF %ERRORLEVEL% NEQ 0 exit /b 2
         echo    - Dependencies are installed.
    goto :eof
    """
    
def get_uv_run_sh_template():
        return """
#!/bin/bash
echo "============================================"
echo "     {project_name} (Setup & Run - UV)"
echo "============================================"
echo ""

# --- STAGE 1: Prepare Environment ---
if [ ! -d ".venv" ]; then
    echo "   - .venv not found. Creating now..."
    uv venv
    if [ $? -ne 0 ]; then exit 1; fi
fi

echo "   - Syncing dependencies..."
# Check if requirements.in exists before trying to compile
if [ -f "requirements.in" ]; then
    uv pip compile requirements.in -o requirements.txt
fi
uv pip sync requirements.txt --quiet
if [ $? -ne 0 ]; then exit 1; fi

# --- STAGE 2: Run Application ---
echo ""
echo "--- Starting Application ---"
./.venv/bin/python {launch_file}
"""
    
def get_pip_run_sh_template():
        return """
#!/bin/bash
echo "============================================"
echo "     {project_name} (Run - Pip/Standard)"
echo "============================================"
echo ""

# --- STAGE 1: Prepare Environment ---
if [ ! -d ".venv" ]; then
    echo "   - .venv not found. Creating now..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then exit 1; fi
fi

echo "   - Installing Dependencies..."
if [ -f "requirements.txt" ]; then
    ./.venv/bin/pip install -r requirements.txt --quiet
    if [ $? -ne 0 ]; then exit 1; fi
else
    echo "   [WARNING] requirements.txt not found."
fi

# --- STAGE 2: Run Application ---
echo ""
echo "--- Starting Application ---"
./.venv/bin/python {launch_file}
"""

from typing import List, Tuple

def tests(vfs) -> List[Tuple[str, bool, str]]:
    res =[]
    succ, msg = run(vfs, 'main.py', ['requests'], 'TestProj', {'win', 'unix'})
    passed = succ and vfs.exists('@ROOT/setup_run(uv).bat') and vfs.exists('@ROOT/requirements.in')
    res.append(("Python Env Generate", passed, msg))
    return res
