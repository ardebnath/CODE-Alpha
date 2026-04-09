@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo Python launcher "py" was not found.
    echo Install Python 3.11 or newer, then try again.
    pause
    exit /b 1
)

py -3 -m PyInstaller --noconfirm --clean --windowed --name AlphaLanguageSystemSoftware "%~dp0alpha_desktop_software.py"
if errorlevel 1 (
    echo Build failed.
    echo If PyInstaller is missing, install it with:
    echo py -3 -m pip install pyinstaller
    pause
    exit /b 1
)

echo Build complete.
echo Open the "dist" folder in this directory to find the packaged software.
pause
endlocal
