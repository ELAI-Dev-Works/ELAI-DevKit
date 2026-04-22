#!/bin/bash

clear
echo "========================================================"
echo "                Node.js Installer Helper"
echo "========================================================"
echo ""
echo "[What is Node.js?]"
echo "Node.js is a JavaScript runtime built on Chrome's V8 engine."
echo ""
echo "[Installation Details]"
echo "Method:  Node Version Manager (nvm)"
echo "Command: curl .../install.sh | bash"
echo ""
echo "========================================================"
echo ""
echo "Please select an installation method:"
echo "1. Automatic (Install nvm via curl)"
echo "   - Installs 'nvm', which allows you to install any Node version."
echo "   - After setup, run: nvm install node"
echo ""
echo "2. Manual"
echo "   - Open the official Node.js website."
echo ""

read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "[INFO] Downloading nvm install script..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    
    echo ""
    echo "[INFO] Script executed."
    echo "IMPORTANT: Close and reopen your terminal to start using 'nvm'."
    echo "Then run 'nvm install --lts' to get the latest Node.js."
    read -p "Press Enter to exit..."

elif [ "$choice" = "2" ]; then
    echo ""
    echo "[INFO] Opening https://nodejs.org/ ..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open https://nodejs.org/
    else
        xdg-open https://nodejs.org/
    fi
    read -p "Press Enter to exit..."

else
    echo "Invalid choice."
fi