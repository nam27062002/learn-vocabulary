#!/usr/bin/env python
"""
Database Migration GUI Tool
PyQt6-based GUI for managing database migrations
"""

import sys
import os
import threading
import time
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QTextEdit, QLabel, QProgressBar,
    QGroupBox, QGridLayout, QLineEdit, QCheckBox, QMessageBox,
    QSplitter, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QIcon

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DatabaseMigrationWorker(QThread):
    """Worker thread for database migration"""
    progress_update = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    migration_complete = pyqtSignal(bool, str)
    
    def __init__(self, old_config, new_config, clear_target=True):
        super().__init__()
        self.old_config = old_config
        self.new_config = new_config
        self.clear_target = clear_target
        
    def run(self):
        """Run the migration in background"""
        try:
            self.progress_update.emit("Starting migration...")
            self.progress_value.emit(5)
            
            # Test connections
            self.progress_update.emit("Testing database connections...")
            if not self.test_connections():
                self.migration_complete.emit(False, "Connection test failed")
                return
                
            self.progress_value.emit(15)
            
            # Clear target database if requested
            if self.clear_target:
                self.progress_update.emit("Clearing target database...")
                if not self.clear_target_database():
                    self.migration_complete.emit(False, "Failed to clear target database")
                    return
                self.progress_value.emit(25)
            
            # Get table list
            self.progress_update.emit("Getting table list...")
            tables = self.get_table_list()
            self.progress_update.emit(f"Found {len(tables)} tables to migrate")
            self.progress_value.emit(30)
            
            # Migrate tables
            failed_tables = []
            for i, table in enumerate(tables):
                progress = 30 + (50 * (i + 1) // len(tables))
                self.progress_value.emit(progress)
                self.progress_update.emit(f"Migrating {table}...")
                
                if not self.migrate_table(table):
                    failed_tables.append(table)
                    self.progress_update.emit(f"  [ERROR] Failed to migrate {table}")
                else:
                    self.progress_update.emit(f"  [OK] Successfully migrated {table}")
            
            # Fix sequences
            self.progress_update.emit("Fixing PostgreSQL sequences...")
            self.fix_sequences()
            self.progress_value.emit(90)
            
            # Complete
            self.progress_value.emit(100)
            if failed_tables:
                message = f"Migration completed with {len(failed_tables)} failures: {', '.join(failed_tables)}"
                self.migration_complete.emit(False, message)
            else:
                self.migration_complete.emit(True, "All tables migrated successfully!")
                
        except Exception as e:
            self.migration_complete.emit(False, f"Migration failed: {str(e)}")
    
    def test_connections(self):
        """Test database connections"""
        try:
            # Test old database
            old_conn = psycopg2.connect(**self.old_config)
            old_conn.close()
            self.progress_update.emit("  [OK] Old database connection successful")
            
            # Test new database
            new_conn = psycopg2.connect(**self.new_config)
            new_conn.close()
            self.progress_update.emit("  [OK] New database connection successful")
            
            return True
        except Exception as e:
            self.progress_update.emit(f"  [ERROR] Connection failed: {e}")
            return False
    
    def get_table_list(self):
        """Get list of tables from old database"""
        conn = psycopg2.connect(**self.old_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'django_migrations'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables
    
    def clear_target_database(self):
        """Clear all data from target database"""
        try:
            self.progress_update.emit("Clearing target database...")
            
            conn = psycopg2.connect(**self.new_config)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Disable foreign key constraints
            cursor.execute("SET session_replication_role = replica;")
            
            # Clear all tables
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                self.progress_update.emit(f"  [OK] Cleared {table}")
            
            # Reset sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            sequences = [row[0] for row in cursor.fetchall()]
            
            for seq_name in sequences:
                cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
            
            # Re-enable foreign key constraints
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.progress_update.emit("[OK] Target database cleared completely")
            return True
            
        except Exception as e:
            self.progress_update.emit(f"[ERROR] Failed to clear database: {e}")
            return False

    def migrate_table(self, table_name):
        """Migrate a single table"""
        try:
            # Get data from old database
            old_conn = psycopg2.connect(**self.old_config)
            old_cursor = old_conn.cursor()
            
            old_cursor.execute(f"SELECT * FROM {table_name}")
            column_names = [desc[0] for desc in old_cursor.description]
            rows = old_cursor.fetchall()
            
            old_cursor.close()
            old_conn.close()
            
            if not rows:
                return True
            
            # Insert into new database
            new_conn = psycopg2.connect(**self.new_config)
            new_cursor = new_conn.cursor()
            
            # Insert rows (don't truncate if we already cleared the whole database)
            placeholders = ', '.join(['%s'] * len(column_names))
            columns = ', '.join(column_names)
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            new_cursor.executemany(query, rows)
            new_conn.commit()
            
            new_cursor.close()
            new_conn.close()
            
            return True
            
        except Exception as e:
            return False
    
    def fix_sequences(self):
        """Fix PostgreSQL sequences"""
        conn = psycopg2.connect(**self.new_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            
            sequences = [row[0] for row in cursor.fetchall()]
            
            for seq_name in sequences:
                if seq_name.endswith('_id_seq'):
                    table_name = seq_name[:-7]
                    
                    try:
                        cursor.execute(f"SELECT COALESCE(MAX(id), 1) FROM {table_name}")
                        max_id = cursor.fetchone()[0]
                        cursor.execute(f"SELECT setval('{seq_name}', {max_id})")
                    except:
                        pass
            
            conn.commit()
            
        except Exception as e:
            pass
        finally:
            cursor.close()
            conn.close()


class DatabaseMigrationGUI(QMainWindow):
    """Main GUI window for database migration"""
    
    def __init__(self):
        super().__init__()
        self.migration_worker = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Database Migration Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Database Migration Tool")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Splitter for database configs and log
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Database configuration panel
        config_widget = self.create_config_panel()
        splitter.addWidget(config_widget)
        
        # Log and progress panel
        log_widget = self.create_log_panel()
        splitter.addWidget(log_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connections")
        self.test_button.clicked.connect(self.test_connections)
        button_layout.addWidget(self.test_button)
        
        self.migrate_button = QPushButton("Start Migration")
        self.migrate_button.clicked.connect(self.start_migration)
        button_layout.addWidget(self.migrate_button)
        
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        
        main_layout.addLayout(button_layout)
        
        # Load default configurations
        self.load_default_configs()
        
    def create_config_panel(self):
        """Create database configuration panel"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Old database config
        old_db_group = QGroupBox("Source Database (Old)")
        old_db_layout = QGridLayout(old_db_group)
        
        old_db_layout.addWidget(QLabel("Host:"), 0, 0)
        self.old_host = QLineEdit("dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com")
        old_db_layout.addWidget(self.old_host, 0, 1)
        
        old_db_layout.addWidget(QLabel("Port:"), 1, 0)
        self.old_port = QLineEdit("5432")
        old_db_layout.addWidget(self.old_port, 1, 1)
        
        old_db_layout.addWidget(QLabel("Database:"), 2, 0)
        self.old_database = QLineEdit("learn_english_db_rjeh")
        old_db_layout.addWidget(self.old_database, 2, 1)
        
        old_db_layout.addWidget(QLabel("User:"), 3, 0)
        self.old_user = QLineEdit("learn_english_db_rjeh_user")
        old_db_layout.addWidget(self.old_user, 3, 1)
        
        old_db_layout.addWidget(QLabel("Password:"), 4, 0)
        self.old_password = QLineEdit("rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8")
        self.old_password.setEchoMode(QLineEdit.EchoMode.Password)
        old_db_layout.addWidget(self.old_password, 4, 1)
        
        config_layout.addWidget(old_db_group)
        
        # New database config
        new_db_group = QGroupBox("Target Database (New)")
        new_db_layout = QGridLayout(new_db_group)
        
        new_db_layout.addWidget(QLabel("Host:"), 0, 0)
        self.new_host = QLineEdit("dpg-d32033juibrs739dn540-a.oregon-postgres.render.com")
        new_db_layout.addWidget(self.new_host, 0, 1)
        
        new_db_layout.addWidget(QLabel("Port:"), 1, 0)
        self.new_port = QLineEdit("5432")
        new_db_layout.addWidget(self.new_port, 1, 1)
        
        new_db_layout.addWidget(QLabel("Database:"), 2, 0)
        self.new_database = QLineEdit("learn_english_db_wuep")
        new_db_layout.addWidget(self.new_database, 2, 1)
        
        new_db_layout.addWidget(QLabel("User:"), 3, 0)
        self.new_user = QLineEdit("learn_english_db_wuep_user")
        new_db_layout.addWidget(self.new_user, 3, 1)
        
        new_db_layout.addWidget(QLabel("Password:"), 4, 0)
        self.new_password = QLineEdit("RSZefSFspMPlsqz5MnxJeeUkKueWjSLH")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        new_db_layout.addWidget(self.new_password, 4, 1)
        
        config_layout.addWidget(new_db_group)
        
        # Options
        options_group = QGroupBox("Migration Options")
        options_layout = QVBoxLayout(options_group)
        
        self.truncate_checkbox = QCheckBox("Truncate tables before migration")
        self.truncate_checkbox.setChecked(True)
        options_layout.addWidget(self.truncate_checkbox)
        
        self.fix_sequences_checkbox = QCheckBox("Fix PostgreSQL sequences after migration")
        self.fix_sequences_checkbox.setChecked(True)
        options_layout.addWidget(self.fix_sequences_checkbox)
        
        self.clear_target_checkbox = QCheckBox("Clear target database before migration (ensures 100% consistency)")
        self.clear_target_checkbox.setChecked(True)
        options_layout.addWidget(self.clear_target_checkbox)
        
        config_layout.addWidget(options_group)
        
        config_layout.addStretch()
        
        return config_widget
        
    def create_log_panel(self):
        """Create log and progress panel"""
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        # Progress bar
        progress_group = QGroupBox("Migration Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to start migration")
        progress_layout.addWidget(self.status_label)
        
        log_layout.addWidget(progress_group)
        
        # Log output
        log_group = QGroupBox("Migration Log")
        log_group_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        log_group_layout.addWidget(self.log_text)
        
        log_layout.addWidget(log_group)
        
        return log_widget
    
    def load_default_configs(self):
        """Load default database configurations"""
        self.log("Database Migration Tool initialized")
        self.log("Default configurations loaded")
        
    def get_old_db_config(self):
        """Get old database configuration"""
        return {
            'host': self.old_host.text(),
            'port': self.old_port.text(),
            'database': self.old_database.text(),
            'user': self.old_user.text(),
            'password': self.old_password.text()
        }
    
    def get_new_db_config(self):
        """Get new database configuration"""
        return {
            'host': self.new_host.text(),
            'port': self.new_port.text(),
            'database': self.new_database.text(),
            'user': self.new_user.text(),
            'password': self.new_password.text()
        }
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready to start migration")
    
    def test_connections(self):
        """Test database connections"""
        self.log("Testing database connections...")
        
        old_config = self.get_old_db_config()
        new_config = self.get_new_db_config()
        
        # Test old database
        try:
            conn = psycopg2.connect(**old_config)
            conn.close()
            self.log("✓ Old database connection successful")
        except Exception as e:
            self.log(f"✗ Old database connection failed: {e}")
            QMessageBox.critical(self, "Connection Error", f"Old database connection failed:\n{e}")
            return
        
        # Test new database
        try:
            conn = psycopg2.connect(**new_config)
            conn.close()
            self.log("✓ New database connection successful")
        except Exception as e:
            self.log(f"✗ New database connection failed: {e}")
            QMessageBox.critical(self, "Connection Error", f"New database connection failed:\n{e}")
            return
            
        self.log("All database connections successful!")
        QMessageBox.information(self, "Success", "All database connections are working!")
    
    def start_migration(self):
        """Start the database migration"""
        # Confirm migration
        reply = QMessageBox.question(
            self, 
            "Confirm Migration", 
            "This will overwrite all data in the target database.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable buttons
        self.test_button.setEnabled(False)
        self.migrate_button.setEnabled(False)
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting migration...")
        
        # Start worker thread
        old_config = self.get_old_db_config()
        new_config = self.get_new_db_config()
        clear_target = self.clear_target_checkbox.isChecked()
        
        self.migration_worker = DatabaseMigrationWorker(old_config, new_config, clear_target)
        self.migration_worker.progress_update.connect(self.log)
        self.migration_worker.progress_value.connect(self.progress_bar.setValue)
        self.migration_worker.migration_complete.connect(self.migration_finished)
        
        self.migration_worker.start()
    
    def migration_finished(self, success, message):
        """Handle migration completion"""
        self.log(f"Migration finished: {message}")
        self.status_label.setText("Migration completed")
        
        # Re-enable buttons
        self.test_button.setEnabled(True)
        self.migrate_button.setEnabled(True)
        
        # Show completion message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Migration Issues", message)


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Database Migration Tool")
    
    # Create and show main window
    window = DatabaseMigrationGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()