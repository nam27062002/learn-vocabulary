"""
Configuration Manager for Database Migration GUI Tool

This module handles saving, loading, and managing database configuration presets
using JSON files. It provides default configurations and allows users to save
their custom settings for future use.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

from PyQt6.QtCore import QSettings


@dataclass
class DatabaseConfigPreset:
    """Database configuration preset with metadata"""
    name: str
    description: str
    engine: str = "django.db.backends.postgresql"
    host: str = ""
    port: str = "5432"
    database_name: str = ""
    username: str = ""
    password: str = ""
    sslmode: str = "require"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    is_default: bool = False


@dataclass
class MigrationConfigPreset:
    """Complete migration configuration including source, target, and options"""
    name: str
    description: str
    migration_type: str  # sqlite_to_env, env_to_sqlite, env_to_new_server
    source_config: Optional[DatabaseConfigPreset] = None
    target_config: Optional[DatabaseConfigPreset] = None
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())


class ConfigurationManager:
    """Manages database configuration presets and application settings"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_presets_file = self.config_dir / "database_presets.json"
        self.migration_presets_file = self.config_dir / "migration_presets.json"
        self.app_settings_file = self.config_dir / "app_settings.json"
        
        # Initialize with default configurations if files don't exist
        self._ensure_default_configs()
    
    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory"""
        # Use user's data directory
        if os.name == 'nt':  # Windows
            config_path = Path(os.environ.get('APPDATA', '')) / "LearnVocabulary" / "DatabaseMigrator"
        else:  # Linux/Mac
            config_path = Path.home() / ".config" / "learn-vocabulary" / "database-migrator"
        
        return config_path
    
    def _ensure_default_configs(self):
        """Create default configuration files if they don't exist"""
        if not self.db_presets_file.exists():
            self._create_default_db_presets()
        
        if not self.migration_presets_file.exists():
            self._create_default_migration_presets()
        
        if not self.app_settings_file.exists():
            self._create_default_app_settings()
    
    def _create_default_db_presets(self):
        """Create default database presets based on the original scripts"""
        default_presets = [
            DatabaseConfigPreset(
                name="Learn English DB (Original Server)",
                description="Original production server from migrate_env_db_to_sqlite.py",
                engine="django.db.backends.postgresql",
                host="dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com",
                port="5432",
                database_name="learn_english_db_rjeh",
                username="learn_english_db_rjeh_user",
                password="rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8",
                sslmode="require",
                is_default=True
            ),
            DatabaseConfigPreset(
                name="Learn English DB (New Server)",
                description="New server from migrate_env_db_to_new_server.py",
                engine="django.db.backends.postgresql",
                host="dpg-d32033juibrs739dn540-a.oregon-postgres.render.com",
                port="5432",
                database_name="learn_english_db_wuep",
                username="learn_english_db_wuep_user",
                password="RSZefSFspMPlsqz5MnxJeeUkKueWjSLH",
                sslmode="require",
                is_default=True
            ),
            DatabaseConfigPreset(
                name="Local SQLite",
                description="Local SQLite database file",
                engine="django.db.backends.sqlite3",
                host="",
                port="",
                database_name="db.sqlite3",
                username="",
                password="",
                sslmode="",
                is_default=True
            ),
            DatabaseConfigPreset(
                name="Local PostgreSQL",
                description="Local PostgreSQL development server",
                engine="django.db.backends.postgresql",
                host="localhost",
                port="5432",
                database_name="learn_english_dev",
                username="postgres",
                password="",
                sslmode="prefer",
                is_default=True
            )
        ]
        
        self.save_database_presets(default_presets)
    
    def _create_default_migration_presets(self):
        """Create default migration presets"""
        db_presets = self.load_database_presets()
        
        # Find default presets
        original_server = next((p for p in db_presets if "Original Server" in p.name), None)
        new_server = next((p for p in db_presets if "New Server" in p.name), None)
        local_sqlite = next((p for p in db_presets if "Local SQLite" in p.name), None)
        
        default_migrations = []
        
        if local_sqlite and original_server:
            default_migrations.append(MigrationConfigPreset(
                name="Local to Production",
                description="Upload local SQLite data to production server",
                migration_type="sqlite_to_env",
                source_config=local_sqlite,
                target_config=original_server,
                options={"keep_dump": False}
            ))
        
        if original_server and local_sqlite:
            default_migrations.append(MigrationConfigPreset(
                name="Production to Local",
                description="Download production data to local SQLite",
                migration_type="env_to_sqlite",
                source_config=original_server,
                target_config=local_sqlite,
                options={"no_wipe": False, "keep_dump": False}
            ))
        
        if original_server and new_server:
            default_migrations.append(MigrationConfigPreset(
                name="Server Migration",
                description="Migrate from original server to new server",
                migration_type="env_to_new_server",
                source_config=original_server,
                target_config=new_server,
                options={"rebuild_schema": True, "keep_dump": False}
            ))
        
        self.save_migration_presets(default_migrations)
    
    def _create_default_app_settings(self):
        """Create default application settings"""
        default_settings = {
            "last_used_db_preset": "",
            "last_migration_type": "sqlite_to_env",
            "auto_load_last_config": True,
            "confirm_dangerous_operations": True,
            "log_level": "info",
            "window_geometry": "",
            "splitter_sizes": [400, 300]
        }
        
        self.save_app_settings(default_settings)
    
    def load_database_presets(self) -> List[DatabaseConfigPreset]:
        """Load database configuration presets from JSON file"""
        try:
            if self.db_presets_file.exists():
                with open(self.db_presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [DatabaseConfigPreset(**preset) for preset in data]
            return []
        except Exception as e:
            print(f"Error loading database presets: {e}")
            return []
    
    def save_database_presets(self, presets: List[DatabaseConfigPreset]):
        """Save database configuration presets to JSON file"""
        try:
            data = [asdict(preset) for preset in presets]
            with open(self.db_presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving database presets: {e}")
    
    def add_database_preset(self, preset: DatabaseConfigPreset):
        """Add a new database preset"""
        presets = self.load_database_presets()
        
        # Update existing preset if name matches
        for i, existing in enumerate(presets):
            if existing.name == preset.name:
                preset.created_at = existing.created_at  # Preserve creation time
                presets[i] = preset
                break
        else:
            presets.append(preset)
        
        self.save_database_presets(presets)
    
    def remove_database_preset(self, name: str):
        """Remove a database preset by name"""
        presets = self.load_database_presets()
        presets = [p for p in presets if p.name != name]
        self.save_database_presets(presets)
    
    def get_database_preset(self, name: str) -> Optional[DatabaseConfigPreset]:
        """Get a specific database preset by name"""
        presets = self.load_database_presets()
        return next((p for p in presets if p.name == name), None)
    
    def load_migration_presets(self) -> List[MigrationConfigPreset]:
        """Load migration configuration presets from JSON file"""
        try:
            if self.migration_presets_file.exists():
                with open(self.migration_presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    presets = []
                    
                    for preset_data in data:
                        # Reconstruct database config objects
                        source_config = None
                        target_config = None
                        
                        if preset_data.get('source_config'):
                            source_config = DatabaseConfigPreset(**preset_data['source_config'])
                        
                        if preset_data.get('target_config'):
                            target_config = DatabaseConfigPreset(**preset_data['target_config'])
                        
                        preset = MigrationConfigPreset(
                            name=preset_data['name'],
                            description=preset_data['description'],
                            migration_type=preset_data['migration_type'],
                            source_config=source_config,
                            target_config=target_config,
                            options=preset_data.get('options', {}),
                            created_at=preset_data.get('created_at', datetime.now().isoformat()),
                            last_used=preset_data.get('last_used', datetime.now().isoformat())
                        )
                        presets.append(preset)
                    
                    return presets
            return []
        except Exception as e:
            print(f"Error loading migration presets: {e}")
            return []
    
    def save_migration_presets(self, presets: List[MigrationConfigPreset]):
        """Save migration configuration presets to JSON file"""
        try:
            data = []
            for preset in presets:
                preset_dict = asdict(preset)
                # Convert nested dataclass objects to dicts
                if preset_dict['source_config']:
                    preset_dict['source_config'] = asdict(preset.source_config)
                if preset_dict['target_config']:
                    preset_dict['target_config'] = asdict(preset.target_config)
                data.append(preset_dict)
            
            with open(self.migration_presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving migration presets: {e}")
    
    def add_migration_preset(self, preset: MigrationConfigPreset):
        """Add a new migration preset"""
        presets = self.load_migration_presets()
        
        # Update existing preset if name matches
        for i, existing in enumerate(presets):
            if existing.name == preset.name:
                preset.created_at = existing.created_at  # Preserve creation time
                presets[i] = preset
                break
        else:
            presets.append(preset)
        
        self.save_migration_presets(presets)
    
    def load_app_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        try:
            if self.app_settings_file.exists():
                with open(self.app_settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading app settings: {e}")
            return {}
    
    def save_app_settings(self, settings: Dict[str, Any]):
        """Save application settings"""
        try:
            with open(self.app_settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving app settings: {e}")
    
    def update_app_setting(self, key: str, value: Any):
        """Update a single application setting"""
        settings = self.load_app_settings()
        settings[key] = value
        self.save_app_settings(settings)
    
    def get_app_setting(self, key: str, default: Any = None) -> Any:
        """Get a single application setting"""
        settings = self.load_app_settings()
        return settings.get(key, default)
    
    def export_configuration(self, file_path: Path):
        """Export all configurations to a single JSON file"""
        config_data = {
            "database_presets": [asdict(p) for p in self.load_database_presets()],
            "migration_presets": [],
            "app_settings": self.load_app_settings(),
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Handle migration presets with nested objects
        for preset in self.load_migration_presets():
            preset_dict = asdict(preset)
            if preset_dict['source_config']:
                preset_dict['source_config'] = asdict(preset.source_config)
            if preset_dict['target_config']:
                preset_dict['target_config'] = asdict(preset.target_config)
            config_data["migration_presets"].append(preset_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def import_configuration(self, file_path: Path, merge: bool = False):
        """Import configurations from a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        if not merge:
            # Replace all configurations
            if "database_presets" in config_data:
                presets = [DatabaseConfigPreset(**p) for p in config_data["database_presets"]]
                self.save_database_presets(presets)
            
            if "app_settings" in config_data:
                self.save_app_settings(config_data["app_settings"])
        else:
            # Merge configurations
            if "database_presets" in config_data:
                existing_presets = self.load_database_presets()
                new_presets = [DatabaseConfigPreset(**p) for p in config_data["database_presets"]]
                
                # Merge by name
                preset_dict = {p.name: p for p in existing_presets}
                for new_preset in new_presets:
                    preset_dict[new_preset.name] = new_preset
                
                self.save_database_presets(list(preset_dict.values()))
            
            if "app_settings" in config_data:
                existing_settings = self.load_app_settings()
                existing_settings.update(config_data["app_settings"])
                self.save_app_settings(existing_settings)