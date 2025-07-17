#!/usr/bin/env python3
"""
Launcher script for 4x4 Color Puzzle Game
This script handles common issues and provides better error messages
"""

import sys
import os

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: This game requires Python 3.6 or higher")
        print(f"You are running Python {sys.version}")
        return False
    return True

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        print("Error: tkinter is not available")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On CentOS/RHEL: sudo yum install tkinter")
        print("On Windows: tkinter should be included with Python")
        return False

def main():
    """Main launcher function"""
    print("4x4 Color Puzzle Game Launcher")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Check tkinter availability
    if not check_tkinter():
        input("Press Enter to exit...")
        return
    
    # Import and run the game
    try:
        print("Loading game...")
        from colorpuzzle import main as game_main
        game_main()
    except ImportError as e:
        print(f"Error: Could not import game: {e}")
        print("Make sure colorpuzzle.py is in the same directory")
    except Exception as e:
        print(f"Error running game: {e}")
        print("Please report this issue on GitHub")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
