#!/bin/bash

clear
echo "========================================================"
echo "                  UV Installer Helper"
echo "========================================================"
echo ""
echo "[What is UV?]"
echo "uv is an extremely fast Python package installer and resolver,"
echo "written in Rust. It replaces pip, pip-tools, and virtualenv."
echo ""
echo "[Installation Details]"
echo "Command: curl -LsSf https://astral.sh/uv/install.sh | sh"
echo ""
echo "========================================================"
echo ""
echo "Please select an installation method:"
echo "1. Automatic (curl | sh)"
echo "   - Downloads and runs the official installation script."
echo ""
echo "2. Manual"
echo "   - Open the official website documentation."
echo ""

read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "[INFO] Running installation command..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "[SUCCESS] Installation completed."
        echo "You may need to restart your terminal or run 'source \$HOME/.cargo/env'"
    else
        echo ""
        echo "[ERROR] Installation failed. Ensure 'curl' is installed."
    fi
    read -p "Press Enter to exit..."

elif [ "$choice" = "2" ]; then
    echo ""
    echo "[INFO] Opening https://docs.astral.sh/uv/ ..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open https://docs.astral.sh/uv/
    else
        xdg-open https://docs.astral.sh/uv/
    fi
    read -p "Press Enter to exit..."

else
    echo "Invalid choice."
fi