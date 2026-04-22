#!/bin/bash
clear

echo "==============================================="
echo "     ELAI-DevKit Environment & Tools Checker"
echo "==============================================="
echo ""

# --- 1. Check for UV (Critical) ---
echo "[1/4] Checking 'uv' package manager..."
if ! command -v uv &> /dev/null; then
    echo "[ERROR] 'uv' is not found in PATH."
    echo "        Please install uv: https://github.com/astral-sh/uv"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi
echo "   - UV found."

# --- 2. Check for NodeJS ---
echo "[2/4] Checking 'Node.js'..."
if ! command -v node &> /dev/null; then
    echo "[WARNING] 'node' is not found in PATH."
else
    echo "   - Node.js found."
fi

# --- 3. Check for NPM ---
echo "[3/4] Checking 'npm'..."
if ! command -v npm &> /dev/null; then
    echo "[WARNING] 'npm' is not found in PATH."
else
    echo "   - npm found."
fi

# --- 4. Virtual Environment & Dependencies ---
echo "[4/4] Ensuring virtual environment..."
if [ ! -d ".venv" ]; then
    echo "   - .venv not found. Creating via uv..."
    uv venv > /dev/null
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "   - Syncing dependencies..."
uv pip sync requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to sync dependencies."
    read -p "Press Enter to exit..."
    exit 2
fi

echo ""
echo "--- Running Python diagnostics script..."
echo ""

./.venv/bin/python diagnostic/check_tools.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Python diagnostics failed."
    read -p "Press Enter to exit..."
    exit 3
fi

echo ""
echo "==============================================="
echo "            Check finished successfully."
echo "==============================================="
echo ""
# read -p "Press Enter to continue..."