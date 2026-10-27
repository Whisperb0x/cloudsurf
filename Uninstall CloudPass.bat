@echo off
rem Removes CloudPass (and older CloudPass versions) from your Community folder.
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 from python.org and tick "Add python.exe to PATH".
    pause
    exit /b 1
)
python build.py --uninstall
echo.
pause
