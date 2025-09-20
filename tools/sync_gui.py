"""
PyQt6 GUI for Database Sync Tool
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QTextEdit, QProgressBar, QGroupBox,
    QCheckBox, QMessageBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from database_manager import DatabaseManager
import logging
from datetime import datetime

class SyncWorker(QThread):
    """Worker thread for database sync operations"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, sync_direction: str, selected_tables: list):
        super().__init__()
        self.sync_direction = sync_direction  # 'server_to_local' or 'local_to_server'
        self.selected_tables = selected_tables
        self.db_manager = DatabaseManager()

    def run(self):
        """Execute sync operation"""
        try:
            success = True
            message = ""

            if self.sync_direction == 'server_to_local':
                success, message = self._sync_server_to_local()
            else:
                success, message = self._sync_local_to_server()

            self.finished.emit(success, message)

        except Exception as e:
            self.finished.emit(False, f"Sync failed: {str(e)}")

    def _sync_server_to_local(self) -> tuple:
        """Sync data from server to local"""
        self.status.emit("Connecting to databases...")

        if not self.db_manager.connect_server():
            return False, "Failed to connect to server database"

        if not self.db_manager.connect_local():
            return False, "Failed to connect to local database"

        total_tables = len(self.selected_tables)

        for i, table in enumerate(self.selected_tables):
            self.status.emit(f"Syncing table: {table}")

            # Clear destination table
            if not self.db_manager.clear_table(table, target_server=False):
                return False, f"Failed to clear local table: {table}"

            # Get data from server
            data = self.db_manager.get_table_data(table, from_server=True)

            # Insert data to local
            if not self.db_manager.insert_data(table, data, target_server=False):
                return False, f"Failed to insert data to local table: {table}"

            progress = int(((i + 1) / total_tables) * 100)
            self.progress.emit(progress)

        self.db_manager.close_connections()
        return True, f"Successfully synced {total_tables} tables from server to local"

    def _sync_local_to_server(self) -> tuple:
        """Sync data from local to server"""
        self.status.emit("Connecting to databases...")

        if not self.db_manager.connect_local():
            return False, "Failed to connect to local database"

        if not self.db_manager.connect_server():
            return False, "Failed to connect to server database"

        total_tables = len(self.selected_tables)

        for i, table in enumerate(self.selected_tables):
            self.status.emit(f"Syncing table: {table}")

            # Clear destination table
            if not self.db_manager.clear_table(table, target_server=True):
                return False, f"Failed to clear server table: {table}"

            # Get data from local
            data = self.db_manager.get_table_data(table, from_server=False)

            # Insert data to server
            if not self.db_manager.insert_data(table, data, target_server=True):
                return False, f"Failed to insert data to server table: {table}"

            progress = int(((i + 1) / total_tables) * 100)
            self.progress.emit(progress)

        self.db_manager.close_connections()
        return True, f"Successfully synced {total_tables} tables from local to server"

class DatabaseSyncGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.sync_worker = None
        self.available_tables = []
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Database Sync Tool - Learn English App")
        self.setGeometry(100, 100, 1200, 800)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #333333;
            }
            QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin: 10px 5px;
                padding: 15px 5px 5px 5px;
                background-color: #fafafa;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: #fafafa;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 8px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QLabel {
                color: #2c3e50;
                font-size: 11px;
                padding: 2px;
            }
            QTextEdit {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                color: #2c3e50;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
                selection-background-color: #3498db;
            }
            QTableWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                gridline-color: #ecf0f1;
                color: #2c3e50;
                font-size: 11px;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #ebf3fd;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
            QSplitter::handle {
                background-color: #bdc3c7;
                width: 3px;
            }
            QSplitter::handle:hover {
                background-color: #95a5a6;
            }
            /* Status-specific button styles */
            QPushButton[class="warning"] {
                background-color: #f39c12;
                color: white;
            }
            QPushButton[class="warning"]:hover {
                background-color: #e67e22;
            }
            QPushButton[class="danger"] {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton[class="danger"]:hover {
                background-color: #c0392b;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Controls
        left_panel = self.create_left_panel()

        # Right panel - Logs and status
        right_panel = self.create_right_panel()

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """Create left control panel"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Connection status
        conn_group = QGroupBox("Database Connections")
        conn_layout = QVBoxLayout(conn_group)

        self.server_status_label = QLabel("⚪ Server: Not tested")
        self.server_status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-weight: bold;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
        """)

        self.local_status_label = QLabel("⚪ Local: Not tested")
        self.local_status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-weight: bold;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
        """)
        self.test_conn_btn = QPushButton("Test Connections")
        self.test_conn_btn.clicked.connect(self.test_connections)

        conn_layout.addWidget(self.server_status_label)
        conn_layout.addWidget(self.local_status_label)
        conn_layout.addWidget(self.test_conn_btn)

        # Table selection
        table_group = QGroupBox("Select Tables to Sync")
        table_layout = QVBoxLayout(table_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_tables)

        self.discover_tables_btn = QPushButton("Discover Tables")
        self.discover_tables_btn.clicked.connect(self.discover_tables)

        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.discover_tables_btn)
        table_layout.addLayout(button_layout)

        # Tables container
        self.table_checkboxes = {}
        self.tables_container = QVBoxLayout()
        table_layout.addLayout(self.tables_container)

        # Add placeholder text
        self.no_tables_label = QLabel("Click 'Discover Tables' to load available tables")
        self.no_tables_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 20px;
                text-align: center;
            }
        """)
        self.tables_container.addWidget(self.no_tables_label)

        # Sync controls
        sync_group = QGroupBox("Sync Operations")
        sync_layout = QVBoxLayout(sync_group)

        self.server_to_local_btn = QPushButton("Server → Local")
        self.server_to_local_btn.clicked.connect(lambda: self.start_sync('server_to_local'))
        self.server_to_local_btn.setProperty("class", "warning")

        self.local_to_server_btn = QPushButton("Local → Server")
        self.local_to_server_btn.clicked.connect(lambda: self.start_sync('local_to_server'))
        self.local_to_server_btn.setProperty("class", "danger")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        sync_layout.addWidget(self.server_to_local_btn)
        sync_layout.addWidget(self.local_to_server_btn)
        sync_layout.addWidget(self.progress_bar)

        left_layout.addWidget(conn_group)
        left_layout.addWidget(table_group)
        left_layout.addWidget(sync_group)
        left_layout.addStretch()

        return left_widget

    def create_right_panel(self):
        """Create right panel with logs and status"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Status display
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 10px;
                border-radius: 6px;
                border: 2px solid #bdc3c7;
            }
        """)
        status_layout.addWidget(self.status_label)

        # Table information
        info_group = QGroupBox("Table Information")
        info_layout = QVBoxLayout(info_group)

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(3)
        self.info_table.setHorizontalHeaderLabels(["Table Name", "Server Rows", "Local Rows"])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.info_table.setMinimumHeight(200)
        info_layout.addWidget(self.info_table)

        self.refresh_info_btn = QPushButton("Refresh Table Info")
        self.refresh_info_btn.clicked.connect(self.refresh_table_info)
        info_layout.addWidget(self.refresh_info_btn)

        # Log display
        log_group = QGroupBox("Sync Logs")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(200)
        self.log_text.setPlaceholderText("Sync logs will appear here...")
        log_layout.addWidget(self.log_text)

        self.clear_log_btn = QPushButton("Clear Logs")
        self.clear_log_btn.clicked.connect(self.clear_logs)
        log_layout.addWidget(self.clear_log_btn)

        right_layout.addWidget(status_group)
        right_layout.addWidget(info_group)
        right_layout.addWidget(log_group)

        return right_widget

    def setup_logging(self):
        """Setup logging to display in GUI"""
        self.log_handler = GuiLogHandler(self.log_text)
        logger = logging.getLogger()
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

    def test_connections(self):
        """Test database connections"""
        self.log("Testing database connections...")
        results = self.db_manager.test_connections()

        if results['server']:
            self.server_status_label.setText("🟢 Server: Connected")
            self.server_status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #d5f4e6;
                    border-radius: 4px;
                    border: 1px solid #27ae60;
                }
            """)
        else:
            self.server_status_label.setText("🔴 Server: Failed")
            self.server_status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #fadbd8;
                    border-radius: 4px;
                    border: 1px solid #e74c3c;
                }
            """)

        if results['local']:
            self.local_status_label.setText("🟢 Local: Connected")
            self.local_status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #d5f4e6;
                    border-radius: 4px;
                    border: 1px solid #27ae60;
                }
            """)
        else:
            self.local_status_label.setText("🔴 Local: Failed")
            self.local_status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #fadbd8;
                    border-radius: 4px;
                    border: 1px solid #e74c3c;
                }
            """)

    def discover_tables(self):
        """Discover available tables from both databases"""
        self.log("Discovering tables from databases...")

        # Test connections first
        results = self.db_manager.test_connections()
        if not results['server'] or not results['local']:
            QMessageBox.warning(self, "Connection Error",
                              "Please test connections first. Both databases must be accessible.")
            return

        # Get tables from both databases
        server_tables = set(self.db_manager.get_all_tables(from_server=True))
        local_tables = set(self.db_manager.get_all_tables(from_server=False))

        # Find common tables
        common_tables = server_tables.intersection(local_tables)
        server_only = server_tables - local_tables
        local_only = local_tables - server_tables

        self.log(f"Found {len(server_tables)} tables in server, {len(local_tables)} in local")
        self.log(f"Common tables: {len(common_tables)}")

        if server_only:
            self.log(f"Server only: {', '.join(sorted(server_only))}")
        if local_only:
            self.log(f"Local only: {', '.join(sorted(local_only))}")

        # Update available tables
        self.available_tables = sorted(list(common_tables))
        self.update_table_checkboxes()

    def update_table_checkboxes(self):
        """Update table selection checkboxes"""
        # Clear existing checkboxes
        for checkbox in self.table_checkboxes.values():
            checkbox.setParent(None)
        self.table_checkboxes.clear()

        # Remove placeholder
        if hasattr(self, 'no_tables_label') and self.no_tables_label:
            self.no_tables_label.setParent(None)

        # Add new checkboxes
        for table in self.available_tables:
            checkbox = QCheckBox(table)
            checkbox.setChecked(True)
            self.table_checkboxes[table] = checkbox
            self.tables_container.addWidget(checkbox)

        if not self.available_tables:
            no_common_label = QLabel("No common tables found between databases")
            no_common_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-style: italic;
                    padding: 20px;
                    text-align: center;
                }
            """)
            self.tables_container.addWidget(no_common_label)

    def select_all_tables(self):
        """Toggle select all tables"""
        if not self.table_checkboxes:
            QMessageBox.information(self, "Info", "Please discover tables first.")
            return

        all_checked = all(cb.isChecked() for cb in self.table_checkboxes.values())
        for checkbox in self.table_checkboxes.values():
            checkbox.setChecked(not all_checked)

    def get_selected_tables(self) -> list:
        """Get list of selected tables"""
        return [table for table, checkbox in self.table_checkboxes.items()
                if checkbox.isChecked()]

    def start_sync(self, direction: str):
        """Start sync operation"""
        selected_tables = self.get_selected_tables()

        if not selected_tables:
            QMessageBox.warning(self, "Warning", "Please select at least one table to sync.")
            return

        # Confirmation dialog
        direction_text = "Server → Local" if direction == 'server_to_local' else "Local → Server"
        target = "local" if direction == 'server_to_local' else "server"

        reply = QMessageBox.question(
            self,
            "Confirm Sync Operation",
            f"Are you sure you want to sync {direction_text}?\n\n"
            f"This will COMPLETELY CLEAR all data in the {target} database tables:\n"
            f"{', '.join(selected_tables)}\n\n"
            f"This operation cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_sync(direction, selected_tables)

    def _execute_sync(self, direction: str, selected_tables: list):
        """Execute the sync operation"""
        # Disable buttons
        self.server_to_local_btn.setEnabled(False)
        self.local_to_server_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Start worker thread
        self.sync_worker = SyncWorker(direction, selected_tables)
        self.sync_worker.progress.connect(self.progress_bar.setValue)
        self.sync_worker.status.connect(self.update_status)
        self.sync_worker.finished.connect(self.sync_finished)
        self.sync_worker.start()

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)
        self.log(message)

    def sync_finished(self, success: bool, message: str):
        """Handle sync completion"""
        # Re-enable buttons
        self.server_to_local_btn.setEnabled(True)
        self.local_to_server_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.status_label.setText("Sync completed successfully")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Sync failed")
            QMessageBox.critical(self, "Error", message)

        self.log(message)
        self.refresh_table_info()

    def refresh_table_info(self):
        """Refresh table information display"""
        self.log("Refreshing table information...")

        if not self.available_tables:
            self.log("No tables available. Please discover tables first.")
            return

        results = self.db_manager.test_connections()
        if not results['server'] or not results['local']:
            self.log("Cannot refresh: Database connections failed")
            return

        self.info_table.setRowCount(len(self.available_tables))

        for i, table in enumerate(self.available_tables):
            server_count = self.db_manager.get_table_count(table, from_server=True)
            local_count = self.db_manager.get_table_count(table, from_server=False)

            self.info_table.setItem(i, 0, QTableWidgetItem(table))
            self.info_table.setItem(i, 1, QTableWidgetItem(str(server_count)))
            self.info_table.setItem(i, 2, QTableWidgetItem(str(local_count)))

            # Color code rows based on count differences
            if server_count != local_count:
                for col in range(3):
                    item = self.info_table.item(i, col)
                    if item:
                        item.setBackground(QColor("#fff2cc"))  # Light yellow for differences

    def clear_logs(self):
        """Clear log display"""
        self.log_text.clear()

    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.ensureCursorVisible()

class GuiLogHandler(logging.Handler):
    """Custom log handler for GUI display"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.append(f"[{timestamp}] {msg}")
        self.text_widget.ensureCursorVisible()

def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Database Sync Tool")
    app.setApplicationVersion("1.0")

    window = DatabaseSyncGUI()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()