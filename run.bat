@echo off
REM SketchCam launcher for Windows — double-click this file, or run:  run.bat
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo Python was not found. Please install Python 3.8+ from https://python.org
    echo and tick "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Installing dependencies (first run only)...
python -m pip install -r requirements.txt

echo.
echo Starting SketchCam...
python sketchcam.py

echo.
pause
