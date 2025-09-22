#!/usr/bin/env python3
"""
Test script to validate the GUI migrator can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import PyQt6
        print("✓ PyQt6 imported successfully")
    except ImportError as e:
        print(f"✗ PyQt6 import failed: {e}")
        return False
    
    try:
        import django
        django.setup()
        print("✓ Django setup successful")
    except Exception as e:
        print(f"✗ Django setup failed: {e}")
        return False
    
    try:
        from tools.migrate_database.gui_migrator import (
            DatabaseConfig, MigrationWorker, DatabaseConfigWidget, 
            MigrationTabWidget, DatabaseMigrationGUI
        )
        print("✓ GUI migrator classes imported successfully")
    except ImportError as e:
        print(f"✗ GUI migrator import failed: {e}")
        return False
    
    return True

def test_database_config():
    """Test DatabaseConfig class."""
    print("\nTesting DatabaseConfig...")
    
    from tools.migrate_database.gui_migrator import DatabaseConfig
    
    config = DatabaseConfig(
        engine="django.db.backends.postgresql",
        name="test_db",
        user="test_user",
        password="test_pass",
        host="localhost",
        port="5432"
    )
    
    print(f"✓ DatabaseConfig created: {config.name}@{config.host}:{config.port}")
    return True

def test_gui_creation():
    """Test that GUI components can be created (without showing)."""
    print("\nTesting GUI creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from tools.migrate_database.gui_migrator import DatabaseMigrationGUI
        
        # Create QApplication (required for any Qt widgets)
        app = QApplication([])
        
        # Create main window (but don't show it)
        window = DatabaseMigrationGUI()
        print("✓ Main GUI window created successfully")
        
        # Test that tabs were created
        tab_count = window.tab_widget.count()
        print(f"✓ {tab_count} migration tabs created")
        
        # Clean up
        app.quit()
        return True
        
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Database Migration GUI - Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_database_config,
        test_gui_creation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The GUI migrator is ready to use.")
        print("\nTo start the GUI, run:")
        print(f"  .\.venv\Scripts\python.exe tools\\migrate_database\\gui_migrator.py")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)