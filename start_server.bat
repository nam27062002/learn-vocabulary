@echo off
cd /d "D:\My Projects\Web\learn-vocabulary"
call .venv\Scripts\activate.bat
python manage.py runserver 8000
