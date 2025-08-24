@echo off
echo ========================================
echo  Install Redis for Learn English App
echo ========================================
echo.

echo Option 1: Install Redis using WSL (Recommended)
echo Option 2: Skip Redis installation (use database cache)
echo.

set /p choice="Choose option (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo Installing WSL and Redis...
    echo Step 1: Installing WSL...
    wsl --install -d Ubuntu
    echo.
    echo Step 2: Please restart your computer, then run this script again
    echo Step 3: After restart, run: wsl
    echo Step 4: In WSL, run: sudo apt update && sudo apt install redis-server
    echo Step 5: Start Redis: sudo service redis-server start
    echo Step 6: Test Redis: redis-cli ping
    echo.
    pause
) else if "%choice%"=="2" (
    echo.
    echo Skipping Redis installation...
    echo Your app will use database cache (slower but works)
    echo To enable Redis later, install it and restart Django
    echo.
    pause
) else (
    echo Invalid choice. Please run the script again.
    pause
)