@echo off
echo 4x4 Color Puzzle - Starting with embedded PyPy...
echo.

REM Check if embedded PyPy exists
if exist "pypy\pypy.exe" (
    echo Using embedded PyPy for better performance...
    "pypy\pypy.exe" colorpuzzle.py
) else if exist "pypy3\pypy3.exe" (
    echo Using embedded PyPy3 for better performance...
    "pypy3\pypy3.exe" colorpuzzle.py
) else (
    echo Embedded PyPy not found, trying system Python...
    python colorpuzzle.py
    if errorlevel 1 (
        echo.
        echo Neither PyPy nor Python found!
        echo Please ensure Python is installed or contact support.
        pause
        exit /b 1
    )
)

echo.
echo Game closed.
pause
