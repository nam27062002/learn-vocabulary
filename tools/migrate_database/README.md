# GUI Database Migrator (PyQt6)

A small PyQt6 GUI that wraps the existing Django migration scripts:

- `dev_tools/migrate_env_db_to_sqlite.py` (Env DB -> Local SQLite)
- `dev_tools/migrate_sqlite_to_env_db.py` (Local SQLite -> Env DB)
- `dev_tools/migrate_env_db_to_new_server.py` (Env DB -> NEW server DB)

This tool provides a simple interface to choose the migration direction, set common flags, optionally override environment database settings, and stream logs.

## Prerequisites

- Python 3.11+ (matches your project)
- Dependencies:
  - PyQt6
  - Django project deps from the root `requirements.txt`

You can install PyQt6 separately to keep your server image slim.

## Install (Windows PowerShell)

```
# In your virtual environment
pip install -r requirements.txt
pip install PyQt6
```

If you prefer, create a small extra requirements file:

```
pip install -r tools/migrate_database/requirements-gui.txt
```

## Run

```
python tools/migrate_database/gui_migrator.py
```

- Check "I'm sure" to proceed (these operations are destructive to the target DB).
- Set optional dump path or keep-dump.
- For Env -> SQLite, you may choose "Do NOT delete db.sqlite3" to just flush.
- For Env -> NEW server, you can set `--rebuild-schema` and/or fill target overrides (name/user/password/host/port).
- Optionally fill source env overrides (DATABASE_*), which will be passed as environment variables to the subprocess.

## Safety Notes

- Target databases will be cleared or truncated before loading.
- Always back up data before running migrations.
- For large datasets, native DB dump/restore might be more efficient than JSON fixtures.

## Troubleshooting

- If you see "Import PyQt6 could not be resolved", install PyQt6 in your active environment.
- Ensure `DJANGO_SETTINGS_MODULE` in scripts is correct (already set to `learn_english_project.settings`).
- Check that PostgreSQL SSL and credentials are correct if connecting to cloud DBs.
