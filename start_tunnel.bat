@echo off
cd /d "D:\My Projects\Web\learn-vocabulary"

echo ============================================
echo   Starting Django + Cloudflare Tunnel
echo ============================================
echo.

start "Django Server" cmd /c "cd /d "D:\My Projects\Web\learn-vocabulary" && call .venv\Scripts\activate.bat && python manage.py runserver 8000"

timeout /t 3 /nobreak >nul

echo Django server started on http://localhost:8000
echo.
echo Starting Cloudflare Tunnel (URL will be sent to Telegram)...
echo.

call .venv\Scripts\activate.bat
python start_tunnel_notify.py
