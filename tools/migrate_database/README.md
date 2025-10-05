# Database Migration GUI

A simple GUI to run the existing database migration scripts in this repository:

- Env ➜ SQLite (local)
- SQLite (local) ➜ Env
- Env ➜ New Server (PostgreSQL)

This wraps the existing scripts:

- `dev_tools/migrate_env_db_to_sqlite.py`
- `dev_tools/migrate_sqlite_to_env_db.py`
- `dev_tools/migrate_env_db_to_new_server.py`

## Launch

From VS Code or PowerShell:

```powershell
# Using Python directly
python .\tools\migrate_database\run_gui.py

# Or via batch helper
.\tools\migrate_database\launch_gui.bat
```

## Notes

- You must explicitly check the confirmation box before running; these operations can clear target databases.
- You can optionally override environment DB settings in the GUI. If left blank, the scripts use environment variables or embedded defaults.
- `Env ➜ New Server` supports target overrides and an option to rebuild schema (DROP/CREATE `public` then migrate) for PostgreSQL.
- Logs are streamed in real-time in the GUI.
