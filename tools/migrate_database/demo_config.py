#!/usr/bin/env python3
"""
Configuration Demo for Database Migration GUI Tool

This script demonstrates the configuration management features including:
- Loading default presets
- Creating custom presets  
- Exporting/importing configurations
- Auto-loading functionality
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

def demo_configuration_features():
    """Demonstrate configuration management features."""
    print("🚀 Database Migration GUI - Configuration Demo")
    print("=" * 60)
    
    try:
        from tools.migrate_database.config_manager import (
            ConfigurationManager, DatabaseConfigPreset
        )
        
        print("1. Creating Configuration Manager...")
        config_manager = ConfigurationManager()
        print("   ✓ Configuration manager initialized")
        print(f"   ✓ Config directory: {config_manager.config_dir}")
        
        print("\n2. Loading Default Database Presets...")
        presets = config_manager.load_database_presets()
        print(f"   ✓ Found {len(presets)} presets:")
        for preset in presets:
            print(f"     - {preset.name}")
            print(f"       Description: {preset.description}")
            print(f"       Host: {preset.host}")
            print(f"       Database: {preset.database_name}")
            print(f"       Is Default: {preset.is_default}")
            print()
        
        print("3. Demonstrating Original Script Settings...")
        print("   From migrate_env_db_to_sqlite.py:")
        original_server = next((p for p in presets if "Original Server" in p.name), None)
        if original_server:
            print(f"     ✓ Host: {original_server.host}")
            print(f"     ✓ Database: {original_server.database_name}")
            print(f"     ✓ User: {original_server.username}")
            print(f"     ✓ Password: {'*' * len(original_server.password)}")
        
        print("\n   From migrate_env_db_to_new_server.py:")
        new_server = next((p for p in presets if "New Server" in p.name), None)
        if new_server:
            print(f"     ✓ Host: {new_server.host}")
            print(f"     ✓ Database: {new_server.database_name}")
            print(f"     ✓ User: {new_server.username}")
            print(f"     ✓ Password: {'*' * len(new_server.password)}")
        
        print("\n4. Creating Custom Preset...")
        custom_preset = DatabaseConfigPreset(
            name="My Development Server",
            description="Custom development database for testing",
            engine="django.db.backends.postgresql",
            host="dev.mycompany.com",
            port="5432",
            database_name="learn_english_dev",
            username="dev_user", 
            password="dev_password123",
            sslmode="prefer"
        )
        
        config_manager.add_database_preset(custom_preset)
        print("   ✓ Custom preset created and saved")
        
        # Verify it was saved
        loaded_custom = config_manager.get_database_preset("My Development Server")
        if loaded_custom:
            print("   ✓ Custom preset verified in storage")
        
        print("\n5. Application Settings Demo...")
        settings = config_manager.load_app_settings()
        print(f"   ✓ Current settings: {len(settings)} items")
        for key, value in settings.items():
            print(f"     - {key}: {value}")
        
        print("\n6. Export/Import Demo...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = Path(f.name)
        
        try:
            config_manager.export_configuration(export_file)
            print(f"   ✓ Configuration exported to: {export_file}")
            
            # Show export content preview
            with open(export_file, 'r') as f:
                export_data = json.load(f)
                
            print(f"   ✓ Export contains:")
            print(f"     - {len(export_data.get('database_presets', []))} database presets")
            print(f"     - {len(export_data.get('migration_presets', []))} migration presets")
            print(f"     - {len(export_data.get('app_settings', {}))} app settings")
            print(f"     - Export timestamp: {export_data.get('export_timestamp', 'N/A')}")
            
        finally:
            if export_file.exists():
                export_file.unlink()
        
        print("\n7. Auto-Load Configuration Demo...")
        auto_load_enabled = config_manager.get_app_setting("auto_load_last_config", True)
        print(f"   ✓ Auto-load enabled: {auto_load_enabled}")
        
        if auto_load_enabled:
            print("   ✓ The GUI will automatically load default configurations:")
            print("     - Original server for downloading data")
            print("     - New server for uploading data")
            print("     - SQLite for local development")
        
        print("\n8. Configuration File Locations...")
        print(f"   ✓ Database presets: {config_manager.db_presets_file}")
        print(f"   ✓ Migration presets: {config_manager.migration_presets_file}")
        print(f"   ✓ App settings: {config_manager.app_settings_file}")
        
        # Check if files exist
        for file_path in [config_manager.db_presets_file, 
                         config_manager.migration_presets_file,
                         config_manager.app_settings_file]:
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"     ✓ {file_path.name}: {size} bytes")
            else:
                print(f"     ✗ {file_path.name}: Not found")
        
        print("\n" + "=" * 60)
        print("🎉 Configuration Demo Complete!")
        print("\nKey Benefits:")
        print("• No need to remember database credentials")
        print("• Embedded settings from your original scripts") 
        print("• Easy sharing of configurations between team members")
        print("• Automatic loading of appropriate defaults")
        print("• Safe storage in user configuration directory")
        print("\nTo use these features:")
        print("1. Run the GUI application")
        print("2. Select presets from the dropdown menus")
        print("3. Save your own custom configurations")
        print("4. Import/export configurations as needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the configuration demo."""
    success = demo_configuration_features()
    
    if success:
        print(f"\n🚀 Ready to launch GUI:")
        print(f"   .\.venv\Scripts\python.exe tools\\migrate_database\\gui_migrator.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)