@echo off
cd /d "D:\My Projects\Web\learn-vocabulary"

echo ============================================
echo   Starting Django + Cloudflare Tunnel
echo ============================================
echo.

start "Django Server" cmd /c "cd /d "D:\My Projects\Web\learn-vocabulary" && call .venv\Scripts\activate.bat && python manage.py runserver 8000"

echo Waiting for Django server to be ready...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s -o nul -w "" http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo   Still waiting...
    goto wait_loop
)

echo Django server is ready on http://localhost:8000
echo.
echo Starting Cloudflare Tunnel (URL will be sent to Telegram)...
echo.

call .venv\Scripts\activate.bat
python start_tunnel_notify.py
