"""
Database Migration GUI Tool - Quick Reference

This module provides a comprehensive PyQt6-based GUI for database migrations.
It combines the functionality of three separate migration scripts into one tool.

Quick Start:
1. Run: .\.venv\Scripts\python.exe tools\migrate_database\gui_migrator.py
2. Choose your migration type in the tabs
3. Configure database connections
4. Start migration with real-time monitoring

Migration Types:
- SQLite → Environment DB: Upload local data to server
- Environment DB → SQLite: Download server data locally  
- Environment DB → New Server: Copy between servers

Safety Features:
- Connection testing before migration
- User confirmation dialogs
- Progress monitoring with stop functionality
- Comprehensive logging
- Data validation

Files:
- gui_migrator.py: Main GUI application
- test_gui.py: Test suite for validation
- launch_gui.bat: Windows launcher script
- run_gui.py: Cross-platform Python launcher
- README.md: Comprehensive documentation

Dependencies:
- PyQt6 (GUI framework)
- Django (ORM and management commands)
- All existing project dependencies

The tool reuses the core migration logic from the original scripts:
- dev_tools/migrate_sqlite_to_env_db.py
- dev_tools/migrate_env_db_to_sqlite.py  
- dev_tools/migrate_env_db_to_new_server.py

For detailed usage instructions, see README.md
"""

__version__ = "1.0.0"
__author__ = "Learn Vocabulary Project"
__description__ = "PyQt6-based Database Migration GUI Tool"