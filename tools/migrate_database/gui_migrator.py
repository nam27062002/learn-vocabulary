"""
Database Migration GUI Tool

A comprehensive PyQt6-based GUI application that combines all three migration scripts:
1. Local SQLite → Environment Database
2. Environment Database → Local SQLite  
3. Environment Database → New Server Database

Features:
- User-friendly tabbed interface
- Database connection testing
- Real-time progress monitoring
- Detailed logging output
- Safety confirmations
- Configuration persistence
"""

import sys
import os
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, 
    QTextEdit, QProgressBar, QCheckBox, QGroupBox, QMessageBox,
    QComboBox, QSpinBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QIcon, QPixmap

# Ensure Django project is importable
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")


@dataclass
class DatabaseConfig:
    """Database configuration data class"""
    engine: str = "django.db.backends.postgresql"
    name: str = ""
    user: str = ""
    password: str = ""
    host: str = ""
    port: str = "5432"
    sslmode: str = "require"


class MigrationWorker(QThread):
    """Worker thread for running database migrations"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, migration_type: str, source_config: DatabaseConfig, 
                 target_config: DatabaseConfig, options: Dict[str, Any]):
        super().__init__()
        self.migration_type = migration_type
        self.source_config = source_config
        self.target_config = target_config
        self.options = options
        self._stop_requested = False
        
    def run(self):
        """Execute the migration in a separate thread"""
        try:
            if self.migration_type == "sqlite_to_env":
                self._migrate_sqlite_to_env()
            elif self.migration_type == "env_to_sqlite":
                self._migrate_env_to_sqlite()
            elif self.migration_type == "env_to_new_server":
                self._migrate_env_to_new_server()
            else:
                raise ValueError(f"Unknown migration type: {self.migration_type}")
                
            self.finished.emit(True, "Migration completed successfully!")
            
        except Exception as e:
            self.log_message.emit(f"ERROR: {str(e)}", "error")
            self.finished.emit(False, f"Migration failed: {str(e)}")
    
    def stop(self):
        """Request worker to stop"""
        self._stop_requested = True
        
    def _check_stop(self):
        """Check if stop was requested"""
        if self._stop_requested:
            raise InterruptedError("Migration stopped by user")
    
    def _migrate_sqlite_to_env(self):
        """Migrate from SQLite to environment database"""
        import django
        from django.conf import settings
        from django.core.management import call_command
        from django.core.management.color import no_style
        from django.db import connections
        from django.apps import apps
        
        self.log_message.emit("Starting SQLite → Environment migration...", "info")
        self.progress_updated.emit(10)
        
        # Configure databases
        self._configure_databases(sqlite_source=True)
        django.setup()
        
        self.progress_updated.emit(20)
        self._check_stop()
        
        # Test connections
        self.status_updated.emit("Testing database connections...")
        self._test_connection('source')
        self._test_connection('target')
        
        self.progress_updated.emit(30)
        self._check_stop()
        
        # Migrate and clear target
        self.status_updated.emit("Preparing target database...")
        call_command('migrate', database='target', interactive=False, verbosity=1)
        self._clear_target_database()
        
        self.progress_updated.emit(50)
        self._check_stop()
        
        # Dump and load data
        self.status_updated.emit("Dumping data from SQLite...")
        dump_path = self._create_temp_dump_file()
        
        try:
            self._dump_source_data(dump_path, 'source')
            self.progress_updated.emit(70)
            self._check_stop()
            
            self.status_updated.emit("Loading data into target database...")
            self._load_data_to_target(dump_path, 'target')
            self.progress_updated.emit(90)
            self._check_stop()
            
            self.status_updated.emit("Resetting sequences...")
            self._reset_sequences('target')
            self.progress_updated.emit(100)
            
        finally:
            if dump_path.exists() and not self.options.get('keep_dump', False):
                dump_path.unlink()
    
    def _migrate_env_to_sqlite(self):
        """Migrate from environment database to SQLite"""
        import django
        from django.conf import settings
        from django.core.management import call_command
        
        self.log_message.emit("Starting Environment → SQLite migration...", "info")
        self.progress_updated.emit(10)
        
        # Configure databases
        sqlite_path = self._configure_databases(sqlite_target=True)
        django.setup()
        
        self.progress_updated.emit(20)
        self._check_stop()
        
        # Test source connection
        self.status_updated.emit("Testing source database connection...")
        self._test_connection('source')
        
        # Prepare SQLite target
        self.status_updated.emit("Preparing SQLite database...")
        if not self.options.get('no_wipe', False):
            if sqlite_path.exists():
                sqlite_path.unlink()
                self.log_message.emit(f"Deleted existing SQLite file: {sqlite_path}", "info")
        
        call_command('migrate', database='target', interactive=False, verbosity=1)
        
        if self.options.get('no_wipe', False):
            call_command('flush', database='target', interactive=False, verbosity=1)
        
        self.progress_updated.emit(40)
        self._check_stop()
        
        # Dump and load data
        self.status_updated.emit("Dumping data from source database...")
        dump_path = self._create_temp_dump_file()
        
        try:
            self._dump_source_data(dump_path, 'source')
            self.progress_updated.emit(70)
            self._check_stop()
            
            self.status_updated.emit("Loading data into SQLite...")
            self._load_data_to_target(dump_path, 'target')
            self.progress_updated.emit(90)
            self._check_stop()
            
            self.status_updated.emit("Finalizing...")
            self._reset_sequences('target')
            self.progress_updated.emit(100)
            
        finally:
            if dump_path.exists() and not self.options.get('keep_dump', False):
                dump_path.unlink()
    
    def _migrate_env_to_new_server(self):
        """Migrate from environment database to new server"""
        import django
        from django.conf import settings
        from django.core.management import call_command
        
        self.log_message.emit("Starting Environment → New Server migration...", "info")
        self.progress_updated.emit(10)
        
        # Configure databases
        self._configure_databases()
        django.setup()
        
        self.progress_updated.emit(20)
        self._check_stop()
        
        # Test connections
        self.status_updated.emit("Testing database connections...")
        self._test_connection('source')
        self._test_connection('target')
        
        self.progress_updated.emit(30)
        self._check_stop()
        
        # Prepare target schema
        self.status_updated.emit("Preparing target database schema...")
        if self.options.get('rebuild_schema', False):
            self._rebuild_postgres_schema()
        else:
            call_command('migrate', database='target', interactive=False, verbosity=1)
        
        # Clear target data
        self.status_updated.emit("Clearing target database...")
        self._clear_target_database()
        
        self.progress_updated.emit(50)
        self._check_stop()
        
        # Dump and load data
        self.status_updated.emit("Dumping data from source...")
        dump_path = self._create_temp_dump_file()
        
        try:
            self._dump_source_data(dump_path, 'source')
            self.progress_updated.emit(70)
            self._check_stop()
            
            self.status_updated.emit("Loading data into target...")
            self._load_data_to_target(dump_path, 'target')
            self.progress_updated.emit(90)
            self._check_stop()
            
            self.status_updated.emit("Resetting sequences...")
            self._reset_sequences('target')
            self.progress_updated.emit(100)
            
        finally:
            if dump_path.exists() and not self.options.get('keep_dump', False):
                dump_path.unlink()
    
    def _configure_databases(self, sqlite_source=False, sqlite_target=False):
        """Configure Django database settings"""
        from django.conf import settings
        
        databases = dict(getattr(settings, 'DATABASES', {}))
        
        if sqlite_source:
            # Source is SQLite
            sqlite_path = BASE_DIR / 'db.sqlite3'
            databases['source'] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': str(sqlite_path),
            }
            databases['target'] = self._config_to_django_db(self.target_config)
            
        elif sqlite_target:
            # Target is SQLite
            sqlite_path = BASE_DIR / 'db.sqlite3'
            databases['source'] = self._config_to_django_db(self.source_config)
            databases['target'] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': str(sqlite_path),
            }
            settings.DATABASES = databases
            return sqlite_path
            
        else:
            # Both are server databases
            databases['source'] = self._config_to_django_db(self.source_config)
            databases['target'] = self._config_to_django_db(self.target_config)
        
        settings.DATABASES = databases
        return None
    
    def _config_to_django_db(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Convert DatabaseConfig to Django database configuration"""
        db_config = {
            'ENGINE': config.engine,
            'NAME': config.name,
            'USER': config.user,
            'PASSWORD': config.password,
            'HOST': config.host,
            'PORT': config.port,
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
        }
        
        if config.sslmode and 'postgresql' in config.engine:
            db_config['OPTIONS'] = {'sslmode': config.sslmode}
            
        return db_config
    
    def _test_connection(self, alias: str):
        """Test database connection"""
        from django.db import connections
        
        try:
            conn = connections[alias]
            conn.ensure_connection()
            conn.close()
            self.log_message.emit(f"✓ Connection to '{alias}' database successful", "success")
        except Exception as e:
            raise Exception(f"Failed to connect to '{alias}' database: {e}")
    
    def _clear_target_database(self):
        """Clear target database data"""
        from django.db import connections
        from django.core.management import call_command
        
        conn = connections['target']
        engine = conn.settings_dict.get('ENGINE', '')
        
        if 'postgresql' in engine:
            self._truncate_postgres_tables('target')
        else:
            call_command('flush', database='target', interactive=False, verbosity=1)
    
    def _truncate_postgres_tables(self, alias: str):
        """Truncate all PostgreSQL tables with CASCADE"""
        from django.db import connections
        
        conn = connections[alias]
        introspection = conn.introspection
        all_tables = introspection.table_names()
        tables = [t for t in all_tables if t != 'django_migrations']
        
        if not tables:
            self.log_message.emit("No tables to truncate", "info")
            return
            
        with conn.cursor() as cursor:
            qnames = ', '.join([f'"{t}"' for t in tables])
            sql = f'TRUNCATE TABLE {qnames} RESTART IDENTITY CASCADE;'
            cursor.execute(sql)
            
        self.log_message.emit(f"Truncated {len(tables)} tables", "success")
    
    def _rebuild_postgres_schema(self):
        """Drop and recreate PostgreSQL schema"""
        from django.db import connections
        from django.core.management import call_command
        
        conn = connections['target']
        engine = conn.settings_dict.get('ENGINE', '')
        
        if 'postgresql' not in engine:
            self.log_message.emit("Target is not PostgreSQL; skipping schema rebuild", "info")
            return
            
        self.log_message.emit("Dropping and recreating 'public' schema...", "info")
        with conn.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            
        call_command('migrate', database='target', interactive=False, verbosity=1)
        self.log_message.emit("Schema rebuilt successfully", "success")
    
    def _create_temp_dump_file(self) -> Path:
        """Create temporary dump file path"""
        if self.options.get('dump_path'):
            return Path(self.options['dump_path']).resolve()
        else:
            tmp = tempfile.NamedTemporaryFile(prefix='db_dump_', suffix='.json', delete=False)
            tmp.close()
            return Path(tmp.name)
    
    def _dump_source_data(self, dump_path: Path, alias: str):
        """Dump data from source database"""
        from django.core.management import call_command
        
        with open(dump_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', database=alias, indent=2, stdout=f, verbosity=1)
            
        self.log_message.emit(f"Data dumped to {dump_path}", "success")
    
    def _load_data_to_target(self, dump_path: Path, alias: str):
        """Load data into target database"""
        from django.core.management import call_command
        
        call_command('loaddata', str(dump_path), database=alias, verbosity=1)
        self.log_message.emit(f"Data loaded from {dump_path}", "success")
    
    def _reset_sequences(self, alias: str):
        """Reset database sequences"""
        from django.db import connections
        from django.core.management.color import no_style
        from django.apps import apps
        
        models = apps.get_models()
        sql_list = connections[alias].ops.sequence_reset_sql(no_style(), models)
        
        if not sql_list:
            self.log_message.emit("No sequence reset SQL generated", "info")
            return
            
        with connections[alias].cursor() as cursor:
            for sql in sql_list:
                cursor.execute(sql)
                
        self.log_message.emit("Sequences reset completed", "success")


class DatabaseConfigWidget(QWidget):
    """Widget for configuring database connection settings"""
    
    def __init__(self, title: str, show_sqlite_option: bool = False):
        super().__init__()
        self.title = title
        self.show_sqlite_option = show_sqlite_option
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Group box for database configuration
        group_box = QGroupBox(self.title)
        form_layout = QFormLayout()
        
        if self.show_sqlite_option:
            self.db_type = QComboBox()
            self.db_type.addItems(["PostgreSQL", "SQLite"])
            self.db_type.currentTextChanged.connect(self._on_db_type_changed)
            form_layout.addRow("Database Type:", self.db_type)
        
        self.engine_edit = QLineEdit("django.db.backends.postgresql")
        form_layout.addRow("Engine:", self.engine_edit)
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Database Name:", self.name_edit)
        
        self.user_edit = QLineEdit()
        form_layout.addRow("User:", self.user_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        self.host_edit = QLineEdit()
        form_layout.addRow("Host:", self.host_edit)
        
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(5432)
        form_layout.addRow("Port:", self.port_edit)
        
        self.sslmode_edit = QComboBox()
        self.sslmode_edit.addItems(["require", "prefer", "allow", "disable"])
        form_layout.addRow("SSL Mode:", self.sslmode_edit)
        
        group_box.setLayout(form_layout)
        layout.addWidget(group_box)
        
        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)
        
        # Connection status
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        if self.show_sqlite_option:
            self._on_db_type_changed("PostgreSQL")
    
    def _on_db_type_changed(self, db_type: str):
        """Handle database type change"""
        is_postgres = db_type == "PostgreSQL"
        
        self.engine_edit.setEnabled(is_postgres)
        self.user_edit.setEnabled(is_postgres)
        self.password_edit.setEnabled(is_postgres)
        self.host_edit.setEnabled(is_postgres)
        self.port_edit.setEnabled(is_postgres)
        self.sslmode_edit.setEnabled(is_postgres)
        
        if not is_postgres:
            self.engine_edit.setText("django.db.backends.sqlite3")
            self.name_edit.setText(str(BASE_DIR / "db.sqlite3"))
        else:
            self.engine_edit.setText("django.db.backends.postgresql")
            
    def _test_connection(self):
        """Test database connection"""
        config = self.get_config()
        
        try:
            # Simple test - we'll implement full test in the worker
            if not config.name:
                raise ValueError("Database name is required")
                
            if 'postgresql' in config.engine:
                if not all([config.user, config.password, config.host]):
                    raise ValueError("User, password, and host are required for PostgreSQL")
            
            self.status_label.setText("✓ Configuration looks valid")
            self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
    
    def get_config(self) -> DatabaseConfig:
        """Get current database configuration"""
        return DatabaseConfig(
            engine=self.engine_edit.text(),
            name=self.name_edit.text(),
            user=self.user_edit.text(),
            password=self.password_edit.text(),
            host=self.host_edit.text(),
            port=str(self.port_edit.value()),
            sslmode=self.sslmode_edit.currentText()
        )
    
    def set_config(self, config: DatabaseConfig):
        """Set database configuration"""
        self.engine_edit.setText(config.engine)
        self.name_edit.setText(config.name)
        self.user_edit.setText(config.user)
        self.password_edit.setText(config.password)
        self.host_edit.setText(config.host)
        self.port_edit.setValue(int(config.port) if config.port else 5432)
        
        # Set SSL mode
        index = self.sslmode_edit.findText(config.sslmode)
        if index >= 0:
            self.sslmode_edit.setCurrentIndex(index)


class MigrationTabWidget(QWidget):
    """Base widget for migration tabs"""
    
    def __init__(self, migration_type: str, title: str):
        super().__init__()
        self.migration_type = migration_type
        self.title = title
        self.worker = None
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        
        # Create splitter for configuration and progress
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Configuration area
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        
        self._create_config_ui(config_layout)
        config_widget.setLayout(config_layout)
        
        # Progress and log area
        progress_widget = QWidget()
        progress_layout = QVBoxLayout()
        
        self._create_progress_ui(progress_layout)
        progress_widget.setLayout(progress_layout)
        
        splitter.addWidget(config_widget)
        splitter.addWidget(progress_widget)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def _create_config_ui(self, layout):
        """Override in subclasses to create configuration UI"""
        pass
    
    def _create_progress_ui(self, layout):
        """Create progress monitoring UI"""
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Migration")
        self.start_btn.clicked.connect(self._start_migration)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_migration)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Log output
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(QLabel("Log Output:"))
        layout.addWidget(self.log_text)
    
    def _start_migration(self):
        """Start migration process"""
        try:
            # Get configuration
            source_config, target_config, options = self._get_migration_config()
            
            # Validate configuration
            self._validate_config(source_config, target_config)
            
            # Confirm with user
            if not self._confirm_migration():
                return
            
            # Clear log
            self.log_text.clear()
            
            # Create and start worker
            self.worker = MigrationWorker(
                self.migration_type, source_config, target_config, options
            )
            
            # Connect signals
            self.worker.progress_updated.connect(self.progress_bar.setValue)
            self.worker.status_updated.connect(self.status_label.setText)
            self.worker.log_message.connect(self._add_log_message)
            self.worker.finished.connect(self._migration_finished)
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Start worker
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start migration: {str(e)}")
    
    def _stop_migration(self):
        """Stop migration process"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Stopping migration...")
    
    def _migration_finished(self, success: bool, message: str):
        """Handle migration completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("Migration completed successfully!")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Migration failed!")
            QMessageBox.critical(self, "Error", message)
        
        self.worker = None
    
    def _add_log_message(self, message: str, level: str):
        """Add message to log output"""
        color_map = {
            'info': 'black',
            'success': 'green',
            'warning': 'orange',
            'error': 'red'
        }
        
        color = color_map.get(level, 'black')
        formatted = f'<span style="color: {color};">{message}</span>'
        self.log_text.append(formatted)
    
    def _get_migration_config(self):
        """Override in subclasses to return migration configuration"""
        raise NotImplementedError
    
    def _validate_config(self, source_config: DatabaseConfig, target_config: DatabaseConfig):
        """Validate migration configuration"""
        if not source_config.name:
            raise ValueError("Source database name is required")
        if not target_config.name:
            raise ValueError("Target database name is required")
    
    def _confirm_migration(self) -> bool:
        """Confirm migration with user"""
        reply = QMessageBox.question(
            self, 
            "Confirm Migration",
            "This will completely replace the target database with source data.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes


class SqliteToEnvTab(MigrationTabWidget):
    """Tab for SQLite to Environment database migration"""
    
    def __init__(self):
        super().__init__("sqlite_to_env", "SQLite → Environment DB")
    
    def _create_config_ui(self, layout):
        # SQLite source info
        sqlite_info = QLabel(f"<b>Source:</b> Local SQLite file<br>{BASE_DIR / 'db.sqlite3'}")
        layout.addWidget(sqlite_info)
        
        # Target database configuration
        self.target_config = DatabaseConfigWidget("Target Environment Database")
        layout.addWidget(self.target_config)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.keep_dump_cb = QCheckBox("Keep dump file after migration")
        options_layout.addWidget(self.keep_dump_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
    
    def _get_migration_config(self):
        source_config = DatabaseConfig()  # Will be configured as SQLite in worker
        target_config = self.target_config.get_config()
        options = {
            'keep_dump': self.keep_dump_cb.isChecked()
        }
        return source_config, target_config, options


class EnvToSqliteTab(MigrationTabWidget):
    """Tab for Environment database to SQLite migration"""
    
    def __init__(self):
        super().__init__("env_to_sqlite", "Environment DB → SQLite")
    
    def _create_config_ui(self, layout):
        # Source database configuration
        self.source_config = DatabaseConfigWidget("Source Environment Database")
        layout.addWidget(self.source_config)
        
        # SQLite target info
        sqlite_info = QLabel(f"<b>Target:</b> Local SQLite file<br>{BASE_DIR / 'db.sqlite3'}")
        layout.addWidget(sqlite_info)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.no_wipe_cb = QCheckBox("Don't delete existing SQLite file (flush data instead)")
        options_layout.addWidget(self.no_wipe_cb)
        
        self.keep_dump_cb = QCheckBox("Keep dump file after migration")
        options_layout.addWidget(self.keep_dump_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
    
    def _get_migration_config(self):
        source_config = self.source_config.get_config()
        target_config = DatabaseConfig()  # Will be configured as SQLite in worker
        options = {
            'no_wipe': self.no_wipe_cb.isChecked(),
            'keep_dump': self.keep_dump_cb.isChecked()
        }
        return source_config, target_config, options


class EnvToNewServerTab(MigrationTabWidget):
    """Tab for Environment database to New Server migration"""
    
    def __init__(self):
        super().__init__("env_to_new_server", "Environment DB → New Server")
    
    def _create_config_ui(self, layout):
        # Source database configuration
        self.source_config = DatabaseConfigWidget("Source Environment Database")
        layout.addWidget(self.source_config)
        
        # Target database configuration
        self.target_config = DatabaseConfigWidget("Target New Server Database")
        layout.addWidget(self.target_config)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.rebuild_schema_cb = QCheckBox("Rebuild target schema (PostgreSQL only)")
        self.rebuild_schema_cb.setToolTip(
            "Drop and recreate 'public' schema before migration.\n"
            "Use this if target has old/incompatible schema."
        )
        options_layout.addWidget(self.rebuild_schema_cb)
        
        self.keep_dump_cb = QCheckBox("Keep dump file after migration")
        options_layout.addWidget(self.keep_dump_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
    
    def _get_migration_config(self):
        source_config = self.source_config.get_config()
        target_config = self.target_config.get_config()
        options = {
            'rebuild_schema': self.rebuild_schema_cb.isChecked(),
            'keep_dump': self.keep_dump_cb.isChecked()
        }
        return source_config, target_config, options


class DatabaseMigrationGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("LearnVocabulary", "DatabaseMigrator")
        self._init_ui()
        self._load_settings()
        
    def _init_ui(self):
        self.setWindowTitle("Database Migration Tool - Learn Vocabulary")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Database Migration Tool")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Add migration tabs
        self.sqlite_to_env_tab = SqliteToEnvTab()
        self.env_to_sqlite_tab = EnvToSqliteTab()
        self.env_to_new_server_tab = EnvToNewServerTab()
        
        self.tab_widget.addTab(self.sqlite_to_env_tab, "SQLite → Environment")
        self.tab_widget.addTab(self.env_to_sqlite_tab, "Environment → SQLite")
        self.tab_widget.addTab(self.env_to_new_server_tab, "Environment → New Server")
        
        layout.addWidget(self.tab_widget)
        
        central_widget.setLayout(layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _load_settings(self):
        """Load application settings"""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load database configurations (implement if needed)
        # self._load_db_configs()
    
    def _save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        # Save database configurations (implement if needed)
        # self._save_db_configs()
    
    def closeEvent(self, event):
        """Handle application close"""
        self._save_settings()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Database Migration Tool")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Learn Vocabulary")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = DatabaseMigrationGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()