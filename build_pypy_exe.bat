@echo off
echo Building high-performance executable with PyPy...
echo ================================================
echo.

REM Check if PyPy is available
pypy --version >nul 2>&1
if errorlevel 1 (
    echo PyPy not found in PATH. Trying pypy3...
    pypy3 --version >nul 2>&1
    if errorlevel 1 (
        echo Neither pypy nor pypy3 found in PATH.
        echo.
        echo To build with PyPy performance:
        echo 1. Download PyPy from https://pypy.org/download.html
        echo 2. Add PyPy to your PATH, or
        echo 3. Use the full path to pypy.exe in this script
        echo.
        echo Falling back to regular Python build...
        call build_exe.bat
        goto :end
    ) else (
        set PYPY_CMD=pypy3
    )
) else (
    set PYPY_CMD=pypy
)

echo Found PyPy! Installing PyInstaller for PyPy...
%PYPY_CMD% -m pip install pyinstaller

echo.
echo Building executable with PyPy performance...
%PYPY_CMD% -m PyInstaller --onefile --windowed --name "4x4ColorPuzzle-PyPy" colorpuzzle.py

echo.
echo PyPy-optimized executable created!
echo Location: dist\4x4ColorPuzzle-PyPy.exe
echo.
echo This executable includes PyPy's performance benefits
echo without requiring users to install PyPy separately.
echo.

:end
pause
