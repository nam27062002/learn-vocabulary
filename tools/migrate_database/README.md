# Database Migration GUI Tool

A comprehensive PyQt6-based GUI application that combines all database migration scripts into one user-friendly interface.

## Features

- **Three Migration Types:**
  - SQLite → Environment Database
  - Environment Database → SQLite  
  - Environment Database → New Server Database

- **User-Friendly Interface:**
  - Tabbed interface for different migration types
  - Database connection configuration and testing
  - Real-time progress monitoring
  - Detailed logging output
  - Safety confirmations

- **Advanced Options:**
  - Schema rebuilding for PostgreSQL targets
  - Dump file preservation
  - SQLite file management options

## Requirements

- Python 3.7+
- PyQt6
- Django
- All dependencies from the main project

## Installation

The GUI tool is already part of your Learn Vocabulary project. PyQt6 should already be installed in your virtual environment.

If you need to install PyQt6 separately:

```bash
pip install PyQt6
```

## Usage

### Quick Start

1. **Run the GUI application:**
   ```bash
   # From the project root directory
   "D:/My Projects/Web/learn-vocabulary/.venv/Scripts/python.exe" tools/migrate_database/gui_migrator.py
   ```

2. **Choose your migration type** by clicking on the appropriate tab:
   - **SQLite → Environment:** Upload local development data to server
   - **Environment → SQLite:** Download server data for local development
   - **Environment → New Server:** Copy data between server databases

3. **Configure database connections:**
   - Fill in the database connection details
   - Click "Test Connection" to verify settings
   - Use the embedded defaults or environment variables

4. **Set migration options:**
   - Choose whether to keep dump files
   - Select schema rebuild options (for PostgreSQL)
   - Configure SQLite file handling

5. **Start migration:**
   - Click "Start Migration"
   - Monitor progress in real-time
   - Review detailed logs
   - Confirm completion

### Database Configuration

#### PostgreSQL Configuration
- **Engine:** `django.db.backends.postgresql`
- **Name:** Database name
- **User:** Database username
- **Password:** Database password
- **Host:** Database host (e.g., `dpg-xxx.oregon-postgres.render.com`)
- **Port:** Database port (usually `5432`)
- **SSL Mode:** Connection security mode

#### SQLite Configuration
The tool automatically uses `db.sqlite3` in your project root directory.

### Migration Types

#### 1. SQLite → Environment Database
**Use Case:** Upload your local development data to a production/staging server.

**Process:**
1. Source: Local `db.sqlite3` file
2. Target: Remote PostgreSQL/other database
3. Migrates schema and all data
4. Resets sequences on target

**Safety:** Target database is completely cleared before loading data.

#### 2. Environment Database → SQLite
**Use Case:** Download production/staging data for local development.

**Process:**
1. Source: Remote PostgreSQL/other database
2. Target: Local `db.sqlite3` file
3. Option to delete or preserve existing SQLite file
4. Migrates schema and all data

**Options:**
- **Don't delete SQLite file:** Preserves the file but clears data via flush
- **Keep dump file:** Saves the JSON dump for inspection

#### 3. Environment Database → New Server
**Use Case:** Move data between different server databases.

**Process:**
1. Source: Current environment database
2. Target: New server database
3. Optional schema rebuilding for PostgreSQL
4. Migrates schema and all data

**Options:**
- **Rebuild schema:** Drops and recreates PostgreSQL schema (recommended for clean migrations)
- **Keep dump file:** Saves the JSON dump for backup

### Safety Features

- **Confirmation dialogs** before destructive operations
- **Connection testing** before migration starts
- **Progress monitoring** with detailed status updates
- **Comprehensive logging** with color-coded messages
- **Stop functionality** to cancel running migrations
- **Data validation** before processing

### Troubleshooting

#### Common Issues

1. **Connection Failed:**
   - Verify database credentials
   - Check network connectivity
   - Ensure database server is running
   - Verify SSL settings for PostgreSQL

2. **Migration Fails:**
   - Check the log output for specific errors
   - Ensure target database has sufficient permissions
   - Verify schema compatibility
   - Try rebuilding schema option for PostgreSQL

3. **Large Datasets:**
   - The tool uses Django's `dumpdata`/`loaddata` which works well for moderate datasets
   - For very large databases, consider using native database tools

4. **Permission Errors:**
   - Ensure database user has CREATE, DROP, INSERT, UPDATE, DELETE permissions
   - For PostgreSQL, user needs schema modification rights

#### Log Messages

- **Green:** Success messages
- **Orange:** Warning messages  
- **Red:** Error messages
- **Black:** Information messages

### Environment Variables

You can override default database settings using environment variables:

```bash
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432
DATABASE_SSLMODE=require
```

### Command Line Alternatives

If you prefer command-line tools, the original scripts are still available:

```bash
# SQLite → Environment
python ./dev_tools/migrate_sqlite_to_env_db.py --yes

# Environment → SQLite  
python ./dev_tools/migrate_env_db_to_sqlite.py --yes

# Environment → New Server
python ./dev_tools/migrate_env_db_to_new_server.py --yes
```

## Architecture

The GUI tool is built with:

- **PyQt6:** Modern, cross-platform GUI framework
- **Threading:** Non-blocking migration operations
- **Django Integration:** Reuses existing Django models and management commands
- **Modular Design:** Separate components for different migration types

### Key Components

- `DatabaseMigrationGUI`: Main application window
- `MigrationTabWidget`: Base class for migration tabs
- `DatabaseConfigWidget`: Database connection configuration
- `MigrationWorker`: Background thread for migration operations

## Screenshots

[Screenshots would go here - the tool provides a clean, professional interface with:]

- Tabbed layout for different migration types
- Form-based database configuration
- Real-time progress bars
- Color-coded logging output
- Professional styling with the Fusion theme

## License

This tool is part of the Learn Vocabulary project and follows the same license terms.