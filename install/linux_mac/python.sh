#!/bin/bash

clear
echo "========================================================"
echo "                Python Installer Helper"
echo "========================================================"
echo ""
echo "[What is Python?]"
echo "Python is a high-level programming language required for ELAI-DevKit."
echo ""
echo "[Installation Details]"
echo "Linux: apt install python3.x (Debian/Ubuntu)"
echo "macOS: brew install python@3.x (Homebrew)"
echo ""
echo "========================================================"
echo ""
echo "Please select an installation method:"
echo "1. Automatic (apt / brew)"
echo "   - Attempts to install the specified version using system tools."
echo "   - May require sudo/root password."
echo ""
echo "2. Manual"
echo "   - Open the official Python website."
echo ""

read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Common versions: 3.10, 3.11, 3.12, 3.13"
    read -p "Version to install (e.g. 3.11): " py_ver
    
    if [ -z "$py_ver" ]; then
        echo "No version specified."
        exit 1
    fi

    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "[ERROR] Homebrew is not installed. Please install it first: https://brew.sh/"
            exit 1
        fi
        echo "[INFO] Running: brew install python@$py_ver"
        brew install "python@$py_ver"
    else
        # Linux (Assuming Debian/Ubuntu based for apt)
        if command -v apt &> /dev/null; then
            echo "[INFO] Running: sudo apt install python$py_ver"
            echo "You might need to add the deadsnakes PPA for newer versions on older Ubuntu."
            sudo apt update
            sudo apt install "python$py_ver" "python$py_ver-venv" "python$py_ver-dev"
        else
            echo "[ERROR] 'apt' package manager not found. Please install Python manually."
        fi
    fi
    
    echo ""
    echo "[DONE] Check version with: python$py_ver --version"
    read -p "Press Enter to exit..."

elif [ "$choice" = "2" ]; then
    echo ""
    echo "[INFO] Opening https://www.python.org/downloads/ ..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open https://www.python.org/downloads/
    else
        xdg-open https://www.python.org/downloads/
    fi
    read -p "Press Enter to exit..."

else
    echo "Invalid choice."
fi