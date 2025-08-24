@echo off
echo ========================================
echo  Starting Redis Server
echo ========================================
echo.

echo Checking if WSL is available...
wsl --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WSL is not installed or not available.
    echo Please run install_redis.bat first.
    pause
    exit /b 1
)

echo Starting Redis server in WSL...
wsl sudo service redis-server start

echo.
echo Testing Redis connection...
wsl redis-cli ping

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Redis server is running successfully!
    echo You can now start your Django app with: python manage.py runserver
) else (
    echo.
    echo ❌ Redis server failed to start.
    echo Your app will fallback to database cache automatically.
)

echo.
pause