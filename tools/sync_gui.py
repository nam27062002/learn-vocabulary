"""
PyQt6 GUI for Database Sync Tool
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QTextEdit, QProgressBar, QGroupBox,
    QCheckBox, QMessageBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea
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
        QTimer.singleShot(100, self.initial_setup)

    def initial_setup(self):
        """Runs initial setup tasks after a short delay."""
        self.log("🚀 Performing initial auto-setup...")
        self.test_conn_btn.setEnabled(False)
        self.discover_tables_btn.setEnabled(False)
        
        # This will also test connections
        self.discover_tables()
        
        self.test_conn_btn.setEnabled(True)
        self.discover_tables_btn.setEnabled(True)
        self.log("✅ Initial setup complete.")

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Database Sync Tool - Learn English App")
        self.setGeometry(100, 100, 1300, 850)
        self.setFont(QFont('Segoe UI', 9))

        # Set application style (Dark Theme)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #34495e;
                border-radius: 8px;
                margin-top: 10px;
                padding: 20px 5px 5px 5px;
                background-color: #34495e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 2px 8px;
                background-color: #5dade2;
                color: #ffffff;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #5dade2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #8ec3e8;
            }
            QPushButton:pressed {
                background-color: #2c81ba;
            }
            QPushButton:disabled {
                background-color: #566573;
                color: #99a3a4;
            }
            QCheckBox {
                font-size: 12px;
                color: #ecf0f1;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #566573;
                border-radius: 4px;
                background-color: #2c3e50;
            }
            QCheckBox::indicator:hover {
                border-color: #5dade2;
            }
            QCheckBox::indicator:checked {
                background-color: #5dade2;
                border-color: #5dade2;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjY2NjcgMy41TDUuMjUgOS45MTY2N0wyLjMzMzMzIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QLabel {
                color: #ecf0f1;
                font-size: 12px;
                padding: 2px;
            }
            QTextEdit {
                background-color: #283747;
                border: 1px solid #34495e;
                border-radius: 6px;
                color: #ecf0f1;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
                selection-background-color: #5dade2;
            }
            QTableWidget {
                background-color: #34495e;
                border: 1px solid #4a6572;
                border-radius: 6px;
                gridline-color: #4a6572;
                color: #ecf0f1;
                font-size: 12px;
                alternate-background-color: #3a5063;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #4a6572;
            }
            QTableWidget::item:selected {
                background-color: #5dade2; /* Solid accent color */
                color: #ffffff;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #5dade2;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 6px;
                text-align: center;
                background-color: #2c3e50;
                color: #ecf0f1;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #5dade2;
                border-radius: 5px;
            }
            QSplitter::handle {
                background-color: #4a6572;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #5dade2;
            }
            QScrollArea {
                border: none;
                background-color: #34495e;
            }
            /* Status-specific button styles */
            QPushButton[class="warning"] {
                background-color: #f39c12;
            }
            QPushButton[class="warning"]:hover {
                background-color: #f5b041;
            }
            QPushButton[class="danger"] {
                background-color: #e74c3c;
            }
            QPushButton[class="danger"]:hover {
                background-color: #ec7063;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Left panel - Controls
        left_panel = self.create_left_panel()

        # Right panel - Logs and status
        right_panel = self.create_right_panel()

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 850])
        splitter.setHandleWidth(5)

        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """Create left control panel"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)

        # Connection status
        conn_group = QGroupBox("Database Connections")
        conn_layout = QVBoxLayout(conn_group)

        self.server_status_label = QLabel("⚪ Server: Not tested")
        self.server_status_label.setStyleSheet("padding: 5px; border-radius: 4px; font-weight: bold;")

        self.local_status_label = QLabel("⚪ Local: Not tested")
        self.local_status_label.setStyleSheet("padding: 5px; border-radius: 4px; font-weight: bold;")
        
        self.test_conn_btn = QPushButton("🔌 Test Connections")
        self.test_conn_btn.clicked.connect(self.test_connections)

        conn_layout.addWidget(self.server_status_label)
        conn_layout.addWidget(self.local_status_label)
        conn_layout.addWidget(self.test_conn_btn)

        # Table selection
        table_group = QGroupBox("Select Tables to Sync")
        table_layout = QVBoxLayout(table_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select / Deselect All")
        self.select_all_btn.clicked.connect(self.select_all_tables)

        self.discover_tables_btn = QPushButton("🔍 Discover Tables")
        self.discover_tables_btn.clicked.connect(self.discover_tables)

        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.discover_tables_btn)
        table_layout.addLayout(button_layout)

        # Tables container with ScrollArea
        self.table_checkboxes = {}
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        tables_widget = QWidget()
        self.tables_container = QVBoxLayout(tables_widget) # Keep the name
        self.tables_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(tables_widget)
        table_layout.addWidget(scroll_area)

        # Add placeholder text
        self.no_tables_label = QLabel("Click '🔍 Discover Tables' to load tables.")
        self.no_tables_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_tables_label.setStyleSheet("color: #95a5a6; font-style: italic; padding: 20px;")
        self.tables_container.addWidget(self.no_tables_label)

        # Sync controls
        sync_group = QGroupBox("Sync Operations")
        sync_layout = QVBoxLayout(sync_group)

        self.server_to_local_btn = QPushButton("📥 Server → Local")
        self.server_to_local_btn.clicked.connect(lambda: self.start_sync('server_to_local'))
        self.server_to_local_btn.setProperty("class", "warning")

        self.local_to_server_btn = QPushButton("📤 Local → Server")
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
        right_layout.setContentsMargins(5, 0, 0, 0)

        # Status display
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #5dade2;
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
        self.info_table.itemSelectionChanged.connect(self.update_selection_icons)
        info_layout.addWidget(self.info_table)

        self.refresh_info_btn = QPushButton("🔄 Refresh Table Info")
        self.refresh_info_btn.clicked.connect(self.refresh_table_info)
        info_layout.addWidget(self.refresh_info_btn)

        # Log display
        log_group = QGroupBox("Sync Logs")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Sync logs will appear here...")
        log_layout.addWidget(self.log_text)

        self.clear_log_btn = QPushButton("🗑️ Clear Logs")
        self.clear_log_btn.clicked.connect(self.clear_logs)
        log_layout.addWidget(self.clear_log_btn)

        right_layout.addWidget(status_group)
        right_layout.addWidget(info_group)
        right_layout.addWidget(log_group)

        return right_widget

    def update_selection_icons(self):
        """Adds or removes a checkmark prefix based on row selection state."""
        selected_rows = {index.row() for index in self.info_table.selectedIndexes()}
        
        for i in range(self.info_table.rowCount()):
            item = self.info_table.item(i, 0)
            if item is None:
                continue

            text = item.text()
            # Remove existing checkmark to handle deselection or text updates
            if text.startswith('✓ '):
                text = text[2:]

            if i in selected_rows:
                # Add checkmark if not already present
                if not text.startswith('✓ '):
                    item.setText(f'✓ {text}')
            else:
                # Set text back to original (without checkmark)
                item.setText(text)

    def setup_logging(self):
        """Setup logging to display in GUI"""
        self.log_handler = GuiLogHandler(self.log_text)
        logger = logging.getLogger()
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

    def test_connections(self):
        """Test database connections and update UI."""
        self.log("Testing database connections...")
        results = self.db_manager.test_connections()

        if results['server']:
            self.server_status_label.setText("🟢 Server: Connected")
            self.server_status_label.setStyleSheet("""
                color: #2ecc71;
                background-color: #2c3e50;
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #2ecc71;
                font-weight: bold;
            """)
        else:
            self.server_status_label.setText("🔴 Server: Failed")
            self.server_status_label.setStyleSheet("""
                color: #e74c3c;
                background-color: #2c3e50;
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #e74c3c;
                font-weight: bold;
            """)

        if results['local']:
            self.local_status_label.setText("🟢 Local: Connected")
            self.local_status_label.setStyleSheet("""
                color: #2ecc71;
                background-color: #2c3e50;
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #2ecc71;
                font-weight: bold;
            """)
        else:
            self.local_status_label.setText("🔴 Local: Failed")
            self.local_status_label.setStyleSheet("""
                color: #e74c3c;
                background-color: #2c3e50;
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #e74c3c;
                font-weight: bold;
            """)
        return results

    def discover_tables(self):
        """Discover available tables from both databases"""
        self.update_status("Step 1: Testing connections...")
        QApplication.processEvents()

        # Test connections first
        results = self.test_connections()
        if not results['server'] or not results['local']:
            QMessageBox.warning(self, "Connection Error",
                              "Please ensure both database connections are successful before discovering tables.")
            self.update_status("Connection test failed. Please check settings.")
            return

        self.update_status("Step 2: Discovering tables...")
        QApplication.processEvents()

        # Get tables from both databases
        server_tables = set(self.db_manager.get_all_tables(from_server=True))
        local_tables = set(self.db_manager.get_all_tables(from_server=False))

        # Find common tables
        common_tables = server_tables.intersection(local_tables)
        server_only = server_tables - local_tables
        local_only = local_tables - server_tables

        self.log(f"Found {len(server_tables)} tables in server, {len(local_tables)} in local.")
        self.log(f"Found {len(common_tables)} common tables.")

        if server_only:
            self.log(f"Server-only tables: {', '.join(sorted(server_only))}")
        if local_only:
            self.log(f"Local-only tables: {', '.join(sorted(local_only))}")

        # Update available tables
        self.available_tables = sorted(list(common_tables))
        self.update_table_checkboxes()
        
        self.update_status(f"Found {len(self.available_tables)} common tables.")

    def update_table_checkboxes(self):
        """Update table selection checkboxes"""
        # Clear existing checkboxes from layout
        for checkbox in self.table_checkboxes.values():
            self.tables_container.removeWidget(checkbox)
            checkbox.setParent(None)
        self.table_checkboxes.clear()

        # Add new checkboxes
        if self.available_tables:
            self.no_tables_label.setVisible(False)
            for table in self.available_tables:
                checkbox = QCheckBox(table)
                checkbox.setChecked(True)
                self.table_checkboxes[table] = checkbox
                self.tables_container.addWidget(checkbox)
        else:
            # Show placeholder again if no tables
            self.no_tables_label.setText("No common tables found.")
            self.no_tables_label.setVisible(True)

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
            self.log("No tables available. Discover tables first.")
            self.info_table.setRowCount(0)
            return

        results = self.db_manager.test_connections()
        if not results['server'] or not results['local']:
            self.log("Cannot refresh: Database connections failed.")
            return

        self.info_table.setRowCount(len(self.available_tables))

        for i, table in enumerate(self.available_tables):
            server_count = self.db_manager.get_table_count(table, from_server=True)
            local_count = self.db_manager.get_table_count(table, from_server=False)

            # Create and set items
            item_table = QTableWidgetItem(table)
            item_server = QTableWidgetItem(str(server_count))
            item_local = QTableWidgetItem(str(local_count))

            # Center align count columns
            item_server.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_local.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.info_table.setItem(i, 0, item_table)
            self.info_table.setItem(i, 1, item_server)
            self.info_table.setItem(i, 2, item_local)

            # Color code rows based on count differences
            highlight_color = QColor("#574B2B") # Dark yellow for differences
            transparent_color = QColor("transparent")

            if server_count != local_count:
                for col in range(3):
                    self.info_table.item(i, col).setBackground(highlight_color)
            else:
                for col in range(3):
                    self.info_table.item(i, col).setBackground(transparent_color)

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