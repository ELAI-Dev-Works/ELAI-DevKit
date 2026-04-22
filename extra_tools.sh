#!/bin/bash
cd "$(dirname "$0")"
clear

echo "==========================================="
echo "            Extra Tools Menu"
echo "==========================================="
echo ""

if [ ! -f "./.venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Please run install scripts first."
    read -p "Press Enter to exit..."
    exit 1
fi

scripts=(extra_tools/*.py)
if [ ${#scripts[@]} -eq 0 ] ||[ ! -e "${scripts[0]}" ]; then
    echo "No scripts found in the extra_tools folder."
    read -p "Press Enter to exit..."
    exit 0
fi

idx=1
for script in "${scripts[@]}"; do
    echo "[$idx] $(basename "$script")"
    idx=$((idx + 1))
done

echo ""
read -p "Select a script to run (1-${#scripts[@]}): " choice

if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#scripts[@]}" ]; then
    selected="${scripts[$((choice - 1))]}"
    echo ""
    echo "Running $selected..."
    echo ""
    ./.venv/bin/python "$selected"
else
    echo "Invalid choice."
fi

echo ""
read -p "Press Enter to exit..."