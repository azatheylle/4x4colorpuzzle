@echo off
echo Building 4x4 Color Puzzle executable...
echo This will create a standalone .exe file that others can run without Python installed.
echo.

REM Check if PyInstaller is available
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Create executable with PyInstaller using the spec file
python -m PyInstaller colorpuzzle.spec

echo.
echo Build complete! 
echo The executable is located in the 'dist' folder.
echo You can distribute the entire 'dist' folder or just the .exe file.
echo.
pause
