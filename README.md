# 4x4 Color Puzzle Game

A puzzle game where you use pistons to push colored blocks into their correct corners while keeping the center clear.

## 🎮 How to Play

- **Goal**: Get 3 blocks of each color (Yellow, Blue, Red, Green) into their respective corners
- **Controls**: Click on pistons (arrows around the edge) to extend/retract them
- **Mechanics**: 
  - Pistons can push chains of blocks
  - When retracting, pistons pull one block with their "sticky" face

## 🚀 Quick Start Options

### Option 1: Download Executable (Easiest)
1. Go to the [Releases](../../releases) page
2. Download `4x4ColorPuzzle.exe`
3. Double-click to run - no installation needed!

### Option 2: Run with Python
```bash
# Clone or download this repository
git clone https://github.com/azatheylle/4x4colorpuzzle.git
cd 4x4colorpuzzle

# Run the game (Python 3.6+ required)
python colorpuzzle.py
```

### Option 3: High Performance (PyPy - No Installation Required)
Choose one of these PyPy options for 3-5x faster solving:

**A) Auto-Setup (Easiest)**
```batch
# Downloads and sets up PyPy automatically
auto_setup.bat
```

**B) Portable Distribution**
```batch
# Creates a package with PyPy included (~50MB)
create_portable.bat
```

**C) PyPy Executable**
```batch
# Builds a single .exe with PyPy performance built-in
build_pypy_exe.bat
```

**D) Manual PyPy Setup**
1. Download PyPy from https://pypy.org/download.html
2. Extract to `pypy_portable` folder
3. Run: `run_with_pypy.bat`

## 🎯 Game Features

- **Random Setup**: Each game starts with a randomized puzzle
- **Manual Setup**: Create custom puzzles by placing blocks manually
- **Auto Solver**: Built-in AI solver using A* algorithm
- **Step-by-Step**: Watch the solution execute move by move
- **Clean UI**: Simple, intuitive interface

## 🔧 Building from Source

### Standard Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build standard executable
build_exe.bat
```

### High-Performance Executable (with PyPy)
```bash
# Build executable with PyPy performance (requires PyPy installed)
build_pypy_exe.bat

# Create portable distribution with embedded PyPy
create_portable.bat
```

## 📋 System Requirements

- **For Executable**: Windows 7+ (no additional software needed)
- **For Python**: Python 3.6+ with tkinter (usually included)
- **RAM**: Minimal (< 50MB)
- **Storage**: < 20MB

**Enjoy the puzzle challenge! 🧩**