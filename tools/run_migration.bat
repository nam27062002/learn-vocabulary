@echo off
echo Running Database Migration Tool...
echo.
cd /d "D:\My Projects\Web\learn-vocabulary"
python tools/migrate_database.py
pause