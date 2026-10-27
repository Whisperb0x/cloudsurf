@echo off
rem Copies the CloudSurf package built by the sim (msfs-project\Packages) to
rem your Community folder. Build it first: Dev Mode > open msfs-project\CloudSurf.xml
rem > Build All. Restart the sim afterwards.
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 from python.org and tick "Add python.exe to PATH".
    pause
    exit /b 1
)
python build.py --install
echo.
pause
