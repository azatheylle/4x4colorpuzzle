@echo off
setlocal EnableDelayedExpansion

echo 4x4 Color Puzzle - Auto PyPy Setup
echo ===================================
echo.

REM Check if PyPy is already set up locally
if exist "pypy_portable\pypy.exe" (
    echo PyPy found! Starting game with high performance...
    "pypy_portable\pypy.exe" colorpuzzle.py
    goto :end
)

if exist "pypy_portable\pypy3.exe" (
    echo PyPy3 found! Starting game with high performance...
    "pypy_portable\pypy3.exe" colorpuzzle.py
    goto :end
)

echo PyPy not found locally. Would you like to:
echo.
echo 1. Download and setup PyPy automatically (recommended, ~50MB)
echo 2. Use regular Python
echo 3. Cancel
echo.
set /p choice="Enter choice (1, 2, or 3): "

if "%choice%"=="1" goto :download_pypy
if "%choice%"=="2" goto :use_python
if "%choice%"=="3" goto :end

:download_pypy
echo.
echo Downloading PyPy... (This may take a few minutes)
echo.

REM Create directory
if not exist "pypy_portable" mkdir pypy_portable

REM Note: This would need PowerShell or curl to actually download
echo NOTE: Auto-download requires PowerShell or additional tools.
echo.
echo For now, please:
echo 1. Go to: https://pypy.org/download.html
echo 2. Download "PyPy3.x Windows x86-64"
echo 3. Extract to the "pypy_portable" folder
echo 4. Run this script again
echo.
pause
goto :end

:use_python
echo Using regular Python...
python colorpuzzle.py
if errorlevel 1 (
    echo.
    echo Python not found! Please install Python 3.6+ or setup PyPy.
    pause
)
goto :end

:end
echo.
echo Goodbye!
pause
