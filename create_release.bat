@echo off
echo Creating release package for 4x4 Color Puzzle Game
echo ==================================================
echo.

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist
if not exist "dist\release" mkdir dist\release

echo Step 1: Building executable...
python -m PyInstaller --onefile --windowed --name "4x4ColorPuzzle" --distpath "dist\release" colorpuzzle.py
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

echo.
echo Step 2: Copying additional files...
copy README.md "dist\release\"
copy run_game.bat "dist\release\"
copy launcher.py "dist\release\"
copy colorpuzzle.py "dist\release\"

echo.
echo Step 3: Creating ZIP package...
cd dist\release
powershell Compress-Archive -Path * -DestinationPath "..\4x4ColorPuzzle-Release.zip" -Force
cd ..\..

echo.
echo ===== RELEASE READY! =====
echo.
echo Files created:
echo   - dist\release\4x4ColorPuzzle.exe (standalone executable)
echo   - dist\4x4ColorPuzzle-Release.zip (complete package)
echo.
echo You can distribute either:
echo   1. Just the .exe file (easiest for users)
echo   2. The complete .zip package (includes source code)
echo.
pause
