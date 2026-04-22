#!/bin/bash
cd "$(dirname "$0")"
clear

echo "============================================"
echo "                  ELAI-DevKit"
echo "============================================"
echo ""
echo "[2/2] Handing over to Python Launcher..."
echo ""

# Ensure .venv python exists or try to use system python to bootstrap
PYTHON_CMD="./.venv/bin/python"
if [ ! -f "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

$PYTHON_CMD launch.py "$@"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[ERROR] Launcher exited with error code $EXIT_CODE."
    read -p "Press Enter to exit..."
fi