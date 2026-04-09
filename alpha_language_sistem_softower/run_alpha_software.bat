@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 "%~dp0alpha_desktop_software.py"
    goto :end
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0alpha_desktop_software.py"
    goto :end
)

echo Python 3.11 or newer was not found on PATH.
echo Install a standard Python build that includes tkinter, then run this launcher again.
pause

:end
endlocal
