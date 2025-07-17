@echo off
echo 4x4 Color Puzzle Game - Quick Setup
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.6+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found! Starting game...
echo.

REM Try to run the game
python launcher.py

echo.
echo Game closed.
pause
