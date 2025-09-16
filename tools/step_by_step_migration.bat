@echo off
echo === Database Migration Process ===
echo.
echo This process will:
echo 1. Update your .env file to point to the new database
echo 2. Run Django migrations to create tables
echo 3. Run the data migration tool
echo.

cd /d "D:\My Projects\Web\learn-vocabulary"

echo Step 1: Updating .env file...
echo DATABASE_ENGINE=django.db.backends.postgresql > .env
echo DATABASE_NAME=learn_english_db_wuep >> .env
echo DATABASE_USER=learn_english_db_wuep_user >> .env
echo DATABASE_PASSWORD=RSZefSFspMPlsqz5MnxJeeUkKueWjSLH >> .env
echo DATABASE_HOST=dpg-d32033juibrs739dn540-a.oregon-postgres.render.com >> .env
echo DATABASE_PORT=5432 >> .env
echo [OK] .env file updated

echo.
echo Step 2: Running Django migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo [ERROR] Migrations failed
    pause
    exit /b 1
)
echo [OK] Database schema created

echo.
echo Step 3: Running data migration...
python tools/migrate_database.py

echo.
echo Migration process complete!
pause