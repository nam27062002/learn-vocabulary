@echo off
echo Starting Database Sync Tool...
echo.

cd /d "D:\My Projects\Web\LearnEngish\tools"

echo Checking if dependencies are installed...
pip list | findstr PyQt6 >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Dependencies already installed.
)

echo.
echo Starting GUI...
python sync_gui.py

pause