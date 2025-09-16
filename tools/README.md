# Database Migration Tool

This tool helps migrate all data from your old PostgreSQL database to a new PostgreSQL database.

## Usage

1. **Run the migration tool:**
   ```bash
   cd D:\My Projects\Web\learn-vocabulary
   python tools/migrate_database.py
   ```

2. **The tool will:**
   - Test connections to both databases
   - Show a summary of all tables and row counts
   - Ask for confirmation before proceeding
   - Migrate all data table by table
   - Fix PostgreSQL sequences after migration
   - Provide a detailed summary of the migration results

## Features

- ✅ Tests database connections before starting
- ✅ Shows data summary before migration
- ✅ Requires explicit confirmation (type 'YES')
- ✅ Migrates all tables automatically
- ✅ Handles PostgreSQL sequences properly
- ✅ Provides detailed progress and error reporting
- ✅ Atomic operations (rollback on errors)
- ✅ Clears existing data before inserting new data

## Safety Features

- The tool requires typing 'YES' to confirm the migration
- It shows exactly what will be migrated before starting
- Each table migration is atomic (all or nothing)
- Detailed error reporting for troubleshooting

## Database Configuration

The tool is preconfigured with your database settings:

**Old Database (Source):**
- Host: dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com
- Database: learn_english_db_rjeh

**New Database (Target):**
- Host: dpg-d32033juibrs739dn540-a.oregon-postgres.render.com  
- Database: learn_english_db_wuep

## Prerequisites

Make sure you have the required packages installed:
```bash
pip install psycopg2-binary django
```

## Important Notes

⚠️ **WARNING**: This tool will completely replace all data in the target database. Make sure you have backups if needed.

The migration process:
1. Connects to both databases
2. Gets list of all tables from source database
3. For each table: clears target table and copies all data from source
4. Fixes PostgreSQL sequences to match the migrated data
5. Reports success/failure for each table