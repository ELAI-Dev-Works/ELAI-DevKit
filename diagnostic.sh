#!/bin/bash
cd "$(dirname "$0")"
clear

echo "============================================"
echo "           ELAI-DevKit Diagnostics"
echo "============================================"
echo ""

if[ ! -f "./.venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Please run install scripts first."
    read -p "Press Enter to exit..."
    exit 1
fi

./.venv/bin/python -m systems.diagnostic
read -p "Press Enter to exit..."