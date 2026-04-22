#!/bin/bash

clear
echo "========================================================"
echo "                  Git Installer Helper"
echo "========================================================"
echo ""
echo "[What is Git?]"
echo "Git is a distributed version control system."
echo ""
echo "[Installation Details]"
echo "Linux: apt install git (Debian/Ubuntu)"
echo "macOS: brew install git (Homebrew)"
echo ""
echo "========================================================"
echo ""
echo "Please select an installation method:"
echo "1. Automatic (apt / brew)"
echo "   - Installs Git using the system package manager."
echo ""
echo "2. Manual"
echo "   - Open the official Git website."
echo ""

read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            echo "[ERROR] Homebrew is not installed. Please install it first: https://brew.sh/"
            exit 1
        fi
        echo "[INFO] Running: brew install git"
        brew install git
    else
        # Linux
        if command -v apt &> /dev/null; then
            echo "[INFO] Running: sudo apt install git"
            sudo apt update
            sudo apt install git
        else
            echo "[ERROR] 'apt' package manager not found. Please install Git manually."
        fi
    fi
    
    echo ""
    echo "[DONE] Check version with: git --version"
    read -p "Press Enter to exit..."

elif [ "$choice" = "2" ]; then
    echo ""
    echo "[INFO] Opening https://git-scm.com/downloads ..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open https://git-scm.com/downloads
    else
        xdg-open https://git-scm.com/downloads
    fi
    read -p "Press Enter to exit..."

else
    echo "Invalid choice."
fi