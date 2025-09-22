#!/usr/bin/env python3
"""
Test script for the configuration management system.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

def test_configuration_manager():
    """Test the configuration manager functionality."""
    print("Testing Configuration Manager...")
    
    try:
        from tools.migrate_database.config_manager import (
            ConfigurationManager, DatabaseConfigPreset
        )
        
        # Create a temporary config directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            config_manager = ConfigurationManager(config_dir)
            
            print("✓ Configuration manager created")
            
            # Test loading default presets
            presets = config_manager.load_database_presets()
            print(f"✓ Loaded {len(presets)} default database presets")
            
            # Check if default presets contain the expected ones
            preset_names = [p.name for p in presets]
            expected_names = [
                "Learn English DB (Original Server)",
                "Learn English DB (New Server)",
                "Local SQLite",
                "Local PostgreSQL"
            ]
            
            for expected in expected_names:
                if expected in preset_names:
                    print(f"✓ Found expected preset: {expected}")
                else:
                    print(f"✗ Missing expected preset: {expected}")
                    return False
            
            # Test adding a custom preset
            custom_preset = DatabaseConfigPreset(
                name="Test Database",
                description="Test database configuration",
                engine="django.db.backends.postgresql",
                host="test.example.com",
                port="5432",
                database_name="test_db",
                username="test_user",
                password="test_pass"
            )
            
            config_manager.add_database_preset(custom_preset)
            print("✓ Added custom preset")
            
            # Verify the preset was saved
            loaded_preset = config_manager.get_database_preset("Test Database")
            if loaded_preset and loaded_preset.name == "Test Database":
                print("✓ Custom preset saved and loaded correctly")
            else:
                print("✗ Custom preset not saved correctly")
                return False
            
            # Test app settings
            settings = config_manager.load_app_settings()
            print(f"✓ Loaded app settings: {len(settings)} items")
            
            config_manager.update_app_setting("test_setting", "test_value")
            if config_manager.get_app_setting("test_setting") == "test_value":
                print("✓ App setting update works")
            else:
                print("✗ App setting update failed")
                return False
            
            # Test export/import
            export_file = config_dir / "test_export.json"
            config_manager.export_configuration(export_file)
            
            if export_file.exists():
                print("✓ Configuration export successful")
                
                # Check export content
                with open(export_file, 'r') as f:
                    export_data = json.load(f)
                    
                if "database_presets" in export_data and "app_settings" in export_data:
                    print("✓ Export contains expected data")
                else:
                    print("✗ Export missing expected data")
                    return False
            else:
                print("✗ Configuration export failed")
                return False
            
            return True
            
    except Exception as e:
        print(f"✗ Configuration manager test failed: {e}")
        return False

def test_preset_integration():
    """Test integration between presets and GUI classes."""
    print("\nTesting Preset Integration...")
    
    try:
        from tools.migrate_database.gui_migrator import DatabaseConfig
        from tools.migrate_database.config_manager import DatabaseConfigPreset
        
        # Test conversion between DatabaseConfig and DatabaseConfigPreset
        original_config = DatabaseConfig(
            engine="django.db.backends.postgresql",
            name="test_db",
            user="test_user",
            password="test_pass",
            host="localhost",
            port="5432",
            sslmode="require"
        )
        
        # Convert to preset
        preset = original_config.to_preset("Test Config", "Test description")
        print("✓ DatabaseConfig to preset conversion")
        
        # Convert back to config
        converted_config = DatabaseConfig.from_preset(preset)
        print("✓ Preset to DatabaseConfig conversion")
        
        # Verify data integrity
        if (original_config.engine == converted_config.engine and
            original_config.name == converted_config.name and
            original_config.user == converted_config.user and
            original_config.host == converted_config.host):
            print("✓ Data integrity maintained during conversion")
        else:
            print("✗ Data integrity lost during conversion")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Preset integration test failed: {e}")
        return False

def main():
    """Run configuration tests."""
    print("Database Migration GUI - Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        test_configuration_manager,
        test_preset_integration,
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
    
    print("\n" + "=" * 50)
    print(f"Configuration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All configuration tests passed!")
        print("\nConfiguration features available:")
        print("  - Save/Load database presets")
        print("  - Default configurations from original scripts")
        print("  - Auto-load last used settings")
        print("  - Import/Export configuration files")
        print("  - Configuration validation")
    else:
        print("❌ Some configuration tests failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)