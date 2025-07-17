@echo off
echo Creating portable PyPy distribution...
echo =======================================
echo.

REM Create portable directory structure
if not exist "portable" mkdir portable
if not exist "portable\game" mkdir portable\game
if not exist "portable\pypy" mkdir portable\pypy

echo Step 1: Copying game files...
copy colorpuzzle.py "portable\game\"
copy launcher.py "portable\game\"
copy run_with_pypy.bat "portable\game\"
copy README.md "portable\game\"

echo.
echo Step 2: Instructions for PyPy setup...
echo.
echo TO COMPLETE THE PORTABLE DISTRIBUTION:
echo.
echo 1. Download PyPy from: https://pypy.org/download.html
echo    - Choose: "PyPy3.x Windows x86-64" (or appropriate for your target)
echo.
echo 2. Extract the downloaded PyPy archive
echo.
echo 3. Copy the entire PyPy folder contents to: portable\pypy\
echo    The structure should be:
echo    portable\
echo      game\
echo        colorpuzzle.py
echo        run_with_pypy.bat
echo        ...
echo      pypy\
echo        pypy.exe (or pypy3.exe)
echo        lib\
echo        ...
echo.
echo 4. Test by running: portable\game\run_with_pypy.bat
echo.
echo 5. Distribute the entire "portable" folder as a ZIP file
echo.
echo SIZE NOTE: PyPy adds ~50-100MB to your distribution
echo but eliminates the need for users to install anything!
echo.
pause
