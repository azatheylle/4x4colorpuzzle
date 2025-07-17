#!/bin/bash
# Cross-platform setup script for 4x4 Color Puzzle Game

echo "4x4 Color Puzzle Game - Setup"
echo "============================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.6+ first."
    echo "Visit: https://python.org/downloads/"
    exit 1
fi

echo "Python 3 found!"
python3 --version

# Check if tkinter is available
echo "Checking tkinter availability..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "tkinter is not available. Installing..."
    
    # Detect OS and install tkinter
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y python3-tk
        elif command -v yum &> /dev/null; then
            sudo yum install -y tkinter
        elif command -v pacman &> /dev/null; then
            sudo pacman -S tk
        else
            echo "Could not auto-install tkinter. Please install it manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "On macOS, tkinter should be included with Python."
        echo "If not, try: brew install python-tk"
        exit 1
    fi
fi

echo "tkinter is available!"

# Run the game
echo "Starting game..."
python3 launcher.py
