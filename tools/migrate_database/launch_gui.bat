@echo off
REM Database Migration GUI Launcher for Windows
REM 
REM This batch file launches the PyQt6-based database migration tool.
REM Make sure you run this from the project root directory.

echo Starting Database Migration GUI...
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please make sure you're running this from the project root directory.
    echo And that the virtual environment is set up in .venv\
    pause
    exit /b 1
)

REM Launch the GUI
".venv\Scripts\python.exe" "tools\migrate_database\gui_migrator.py"

REM Check if there was an error
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to start the GUI application.
    echo Error code: %ERRORLEVEL%
    pause
)