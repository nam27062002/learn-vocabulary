@echo off
echo === Complete Fresh Database Migration ===
echo.
echo This tool will:
echo 1. COMPLETELY CLEAR the target database
echo 2. Migrate ALL data from source database
echo 3. Verify 100%% data consistency
echo.
echo WARNING: This will REPLACE all data in target database!
echo.
pause

cd /d "D:\My Projects\Web\learn-vocabulary"
python tools/complete_fresh_migration.py

echo.
echo Migration process completed!
pause