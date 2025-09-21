"""
PyQt6 GUI for Database Sync Tool - Modern UI Version
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QTextEdit, QProgressBar, QGroupBox,
    QCheckBox, QMessageBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QProgressDialog, QLineEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QComboBox, QSpinBox,
    QTabWidget, QFormLayout, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QEasingCurve, QPropertyAnimation,
    QByteArray, QParallelAnimationGroup, QSequentialAnimationGroup, QRect
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QShortcut, QKeySequence,
    QLinearGradient, QPainter, QPen, QBrush, QPixmap
)
from database_manager import DatabaseManager
from sync_worker import SafeSyncWorker
import logging
from datetime import datetime

class DatabaseConfigDialog(QDialog):
    """Dialog for configuring database connection settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Configuration")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        self.load_current_config()

    def setup_ui(self):
        """Setup the configuration dialog UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # PostgreSQL Server Tab
        self.server_tab = QWidget()
        self.setup_server_tab()
        self.tab_widget.addTab(self.server_tab, "PostgreSQL Server")

        # Local Database Tab
        self.local_tab = QWidget()
        self.setup_local_tab()
        self.tab_widget.addTab(self.local_tab, "Local Database")

        # Target PostgreSQL Server Tab (for PG to PG sync)
        self.target_server_tab = QWidget()
        self.setup_target_server_tab()
        self.tab_widget.addTab(self.target_server_tab, "Target PostgreSQL Server")

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_config)

        test_btn = QPushButton("Test Connections")
        test_btn.clicked.connect(self.test_connections)
        button_box.addButton(test_btn, QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(button_box)

        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                background: rgba(255,255,255,0.05);
            }
            QTabBar::tab {
                background: rgba(255,255,255,0.1);
                color: white;
                padding: 8px 16px;
                margin: 2px;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255,0.2);
            }
            QLineEdit, QSpinBox, QComboBox {
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 6px;
                padding: 8px;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4facfe, stop:1 #00f2fe);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6fc5ff, stop:1 #2af5ff);
            }
        """)

    def setup_server_tab(self):
        """Setup PostgreSQL server configuration tab"""
        layout = QFormLayout(self.server_tab)

        self.server_host = QLineEdit()
        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(5432)
        self.server_db = QLineEdit()
        self.server_user = QLineEdit()
        self.server_password = QLineEdit()
        self.server_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Host:", self.server_host)
        layout.addRow("Port:", self.server_port)
        layout.addRow("Database:", self.server_db)
        layout.addRow("Username:", self.server_user)
        layout.addRow("Password:", self.server_password)

    def setup_local_tab(self):
        """Setup local database configuration tab"""
        layout = QFormLayout(self.local_tab)

        self.local_type = QComboBox()
        self.local_type.addItems(["SQLite", "PostgreSQL"])
        self.local_type.currentTextChanged.connect(self.on_local_type_changed)

        self.local_path = QLineEdit()

        # PostgreSQL fields (initially hidden)
        self.local_host = QLineEdit()
        self.local_port = QSpinBox()
        self.local_port.setRange(1, 65535)
        self.local_port.setValue(5432)
        self.local_db = QLineEdit()
        self.local_user = QLineEdit()
        self.local_password = QLineEdit()
        self.local_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Database Type:", self.local_type)
        layout.addRow("SQLite File Path:", self.local_path)

        # PostgreSQL fields
        self.local_host_row = layout.addRow("Host:", self.local_host)
        self.local_port_row = layout.addRow("Port:", self.local_port)
        self.local_db_row = layout.addRow("Database:", self.local_db)
        self.local_user_row = layout.addRow("Username:", self.local_user)
        self.local_password_row = layout.addRow("Password:", self.local_password)

        # Initially hide PostgreSQL fields
        self.on_local_type_changed("SQLite")

    def setup_target_server_tab(self):
        """Setup target PostgreSQL server configuration tab"""
        layout = QFormLayout(self.target_server_tab)

        self.target_host = QLineEdit()
        self.target_port = QSpinBox()
        self.target_port.setRange(1, 65535)
        self.target_port.setValue(5432)
        self.target_db = QLineEdit()
        self.target_user = QLineEdit()
        self.target_password = QLineEdit()
        self.target_password.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Host:", self.target_host)
        layout.addRow("Port:", self.target_port)
        layout.addRow("Database:", self.target_db)
        layout.addRow("Username:", self.target_user)
        layout.addRow("Password:", self.target_password)

        info_label = QLabel("Configure target PostgreSQL server for PostgreSQL-to-PostgreSQL sync")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #4facfe; font-style: italic;")
        layout.addRow(info_label)

    def on_local_type_changed(self, db_type):
        """Handle local database type change"""
        is_sqlite = db_type == "SQLite"

        # Show/hide SQLite fields
        self.local_path.setVisible(is_sqlite)
        local_layout = self.local_tab.layout()
        if local_layout:
            label = local_layout.labelForField(self.local_path)
            if label:
                label.setVisible(is_sqlite)

        # Show/hide PostgreSQL fields
        self.local_host.setVisible(not is_sqlite)
        self.local_port.setVisible(not is_sqlite)
        self.local_db.setVisible(not is_sqlite)
        self.local_user.setVisible(not is_sqlite)
        self.local_password.setVisible(not is_sqlite)

        # Find and hide/show labels
        layout = self.local_tab.layout()
        for i in range(layout.rowCount()):
            item = layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            if item:
                label = item.widget()
                if label and isinstance(label, QLabel):
                    text = label.text()
                    if text in ["Host:", "Port:", "Database:", "Username:", "Password:"]:
                        label.setVisible(not is_sqlite)

    def load_current_config(self):
        """Load current database configuration"""
        # Load from environment or default values
        import os

        # Server config
        self.server_host.setText(os.getenv('DB_HOST', 'localhost'))
        self.server_port.setValue(int(os.getenv('DB_PORT', '5432')))
        self.server_db.setText(os.getenv('DB_NAME', 'learn_english_db'))
        self.server_user.setText(os.getenv('DB_USER', 'postgres'))
        self.server_password.setText(os.getenv('DB_PASSWORD', ''))

        # Local config
        self.local_path.setText('db.sqlite3')

        # Target server config (default to render.com PostgreSQL)
        self.target_host.setText('dpg-d32033juibrs739dn540-a.oregon-postgres.render.com')
        self.target_port.setValue(5432)
        self.target_db.setText('learn_english_db_wuep')
        self.target_user.setText('learn_english_db_wuep_user')
        self.target_password.setText('RSZefSFspMPlsqz5MnxJeeUkKueWjSLH')

    def get_config(self):
        """Get current configuration"""
        return {
            'server': {
                'host': self.server_host.text(),
                'port': self.server_port.value(),
                'database': self.server_db.text(),
                'user': self.server_user.text(),
                'password': self.server_password.text()
            },
            'local': {
                'type': self.local_type.currentText(),
                'path': self.local_path.text(),
                'host': self.local_host.text(),
                'port': self.local_port.value(),
                'database': self.local_db.text(),
                'user': self.local_user.text(),
                'password': self.local_password.text()
            },
            'target_server': {
                'host': self.target_host.text(),
                'port': self.target_port.value(),
                'database': self.target_db.text(),
                'user': self.target_user.text(),
                'password': self.target_password.text()
            }
        }

    def apply_config(self):
        """Apply configuration without closing dialog"""
        config = self.get_config()
        if hasattr(self.parent(), 'apply_database_config'):
            self.parent().apply_database_config(config)
        QMessageBox.information(self, "Configuration", "Database configuration applied successfully!")

    def test_connections(self):
        """Test database connections"""
        config = self.get_config()
        results = []

        # Test server connection
        try:
            from database_manager import DatabaseManager
            db_manager = DatabaseManager()

            # Override config temporarily for testing
            db_manager.server_config = config['server']
            if db_manager.connect_server():
                results.append("✅ PostgreSQL Server: Connection successful")
                db_manager.close_connections()
            else:
                results.append("❌ PostgreSQL Server: Connection failed")
        except Exception as e:
            results.append(f"❌ PostgreSQL Server: {str(e)}")

        # Test local connection
        try:
            if config['local']['type'] == 'SQLite':
                results.append("✅ Local SQLite: Configuration valid")
            else:
                # Test PostgreSQL local connection
                db_manager = DatabaseManager()
                db_manager.local_config = config['local']
                if hasattr(db_manager, 'connect_local_postgresql'):
                    if db_manager.connect_local_postgresql():
                        results.append("✅ Local PostgreSQL: Connection successful")
                        db_manager.close_connections()
                    else:
                        results.append("❌ Local PostgreSQL: Connection failed")
                else:
                    results.append("⚠️ Local PostgreSQL: Feature not implemented yet")
        except Exception as e:
            results.append(f"❌ Local Database: {str(e)}")

        # Test target server connection (if configured)
        if config['target_server']['host']:
            try:
                db_manager = DatabaseManager()
                db_manager.target_server_config = config['target_server']
                if hasattr(db_manager, 'connect_target_server'):
                    if db_manager.connect_target_server():
                        results.append("✅ Target PostgreSQL Server: Connection successful")
                        db_manager.close_connections()
                    else:
                        results.append("❌ Target PostgreSQL Server: Connection failed")
                else:
                    results.append("⚠️ Target PostgreSQL Server: Feature not implemented yet")
            except Exception as e:
                results.append(f"❌ Target PostgreSQL Server: {str(e)}")

        QMessageBox.information(self, "Connection Test Results", "\n".join(results))

class DatabaseSyncGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.sync_worker = None
        self.sync_timer = None
        self.available_tables = []
        self.button_animations = {}  # Store button animations
        self.database_config = None  # Store database configuration
        self.init_ui()
        self.setup_logging()
        self.setup_keyboard_shortcuts()
        QTimer.singleShot(100, self.initial_setup)

    def closeEvent(self, event):
        """Handle application close event"""
        try:
            # Stop sync timer first
            if hasattr(self, 'sync_timer') and self.sync_timer:
                self.sync_timer.stop()
                self.sync_timer = None

            # Stop any running sync
            if hasattr(self, 'sync_worker') and self.sync_worker:
                self.sync_worker.stop()

            # Close database connections
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close_connections()

        except Exception as e:
            print(f"Error during close: {e}")

        event.accept()

    def initial_setup(self):
        """Runs initial setup tasks with a loading dialog."""
        progress = QProgressDialog("Initializing application...", None, 0, 0, self)
        progress.setModal(True)
        progress.setCancelButton(None)
        progress.setWindowFlags(progress.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        progress.setWindowTitle("Loading...")
        progress.show()
        QApplication.processEvents()

        self.log("🚀 Performing initial setup...")

        # Step 1: Test connections only (don't auto-sync)
        self.update_status("Testing connections...")
        results = self.db_manager.test_connections()
        QApplication.processEvents()

        if results['server'] and results['local']:
            self.update_status("Connections successful - Ready to use")
            self.log("✅ Database connections established successfully")
        else:
            self.update_status("Connection issues detected")
            self.log("⚠️ Some database connections failed - check settings")

        progress.close()
        self.log("✅ Initial setup complete.")
        self.update_status("Ready")

    def init_ui(self):
        """Initialize the modern user interface"""
        self.setWindowTitle("🔄 Database Sync Tool - Learn English App")
        self.setGeometry(100, 100, 1200, 750)
        self.setMinimumSize(1000, 600)
        self.setMaximumSize(1400, 900)  # Compact but not too restrictive
        self.setFont(QFont('Inter', 10))  # Modern font

        # Enable all window controls including fullscreen
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowFullscreenButtonHint
        )

        # Set modern application style with enhanced design
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
            }
            QWidget {
                background-color: transparent;
                color: #e8e9ea;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-weight: 400;
            }

            /* More Compact Card-style GroupBox */
            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                border: none;
                border-radius: 8px;
                margin-top: 6px;
                padding: 12px 8px 8px 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255,255,255,0.08), stop:1 rgba(255,255,255,0.04));
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 4px;
                padding: 4px 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }

            /* Ultra Compact Button Design */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                letter-spacing: 0.2px;
                max-height: 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c89f0, stop:1 #8a5cb8);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a6fd8, stop:1 #6b4396);
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.3);
            }

            /* Compact Checkbox */
            QCheckBox {
                font-size: 12px;
                color: #e8e9ea;
                spacing: 8px;
                padding: 4px;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 4px;
                background: rgba(255,255,255,0.05);
            }
            QCheckBox::indicator:hover {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.1);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-color: #667eea;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjY2NjcgMy41TDUuMjUgOS45MTY2N0wyLjMzMzMzIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }

            /* Modern Labels */
            QLabel {
                color: #e8e9ea;
                font-size: 13px;
                padding: 4px;
                font-weight: 500;
            }

            /* Compact Text Input */
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                background: rgba(255,255,255,0.05);
                color: #e8e9ea;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.1);
                outline: none;
            }

            /* Compact Text Area */
            QTextEdit {
                background: rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                color: #e8e9ea;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 11px;
                padding: 12px;
                selection-background-color: #667eea;
                line-height: 1.4;
            }

            /* Compact Table */
            QTableWidget {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                gridline-color: rgba(255,255,255,0.08);
                color: #e8e9ea;
                font-size: 12px;
                font-weight: 500;
                alternate-background-color: rgba(255,255,255,0.02);
            }
            QTableWidget::item {
                padding: 8px 6px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.3), stop:1 rgba(118, 75, 162, 0.3));
                color: #ffffff;
                font-weight: 600;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.2), stop:1 rgba(118, 75, 162, 0.2));
                color: white;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid #667eea;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }

            /* Modern Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 8px;
                text-align: center;
                background: rgba(255,255,255,0.1);
                color: #e8e9ea;
                font-weight: 600;
                height: 16px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }

            /* Modern Splitter */
            QSplitter::handle {
                background: rgba(255,255,255,0.1);
                width: 2px;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background: #667eea;
                width: 4px;
            }

            /* Modern Scroll Area */
            QScrollArea {
                border: none;
                background: transparent;
                border-radius: 12px;
            }
            QScrollArea QWidget {
                background: transparent;
            }

            /* Status-specific button styles with modern gradients */
            QPushButton[class="success"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #56ab2f, stop:1 #a8e6cf);
            }
            QPushButton[class="success"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6bc03e, stop:1 #b8f0df);
            }
            QPushButton[class="warning"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f093fb, stop:1 #f5576c);
            }
            QPushButton[class="warning"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f2a3fc, stop:1 #f6677c);
            }
            QPushButton[class="danger"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff416c, stop:1 #ff4b2b);
            }
            QPushButton[class="danger"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff517c, stop:1 #ff5b3b);
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with compact spacing
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Left panel - Controls
        left_panel = self.create_left_panel()

        # Right panel - Logs and status
        right_panel = self.create_right_panel()

        # Modern splitter with enhanced responsive behavior
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Compact responsive sizing with better balance
        total_width = self.width()
        left_width = min(380, int(total_width * 0.42))  # Slightly wider for better fit
        right_width = total_width - left_width - 24  # Account for margins

        splitter.setSizes([left_width, right_width])
        splitter.setHandleWidth(2)  # Thinner handle
        splitter.setCollapsible(0, False)  # Left panel not collapsible
        splitter.setCollapsible(1, False)  # Right panel not collapsible
        splitter.setStretchFactor(0, 0)   # Left panel fixed ratio
        splitter.setStretchFactor(1, 1)   # Right panel stretchable

        # Store splitter for responsive updates
        self.main_splitter = splitter

        main_layout.addWidget(splitter)

    def resizeEvent(self, event):
        """Handle window resize for responsive design"""
        super().resizeEvent(event)
        if hasattr(self, 'main_splitter'):
            # Adjust splitter sizes on window resize with better proportions
            total_width = self.width()
            left_width = min(380, int(total_width * 0.42))
            right_width = total_width - left_width - 24  # Account for margins and splitter

            self.main_splitter.setSizes([left_width, right_width])

    def create_left_panel(self):
        """Create left control panel"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(10)

        # Connection status with modern styling
        conn_group = QGroupBox("🔗 Database Connections")
        conn_layout = QVBoxLayout(conn_group)
        conn_layout.setSpacing(4)

        self.server_status_label = QLabel("⚪ Server: Not tested")
        self.server_status_label.setStyleSheet("""
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.1);
        """)

        self.local_status_label = QLabel("⚪ Local: Not tested")
        self.local_status_label.setStyleSheet("""
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.1);
        """)

        self.test_conn_btn = QPushButton("🔌 Test Connections")
        self.test_conn_btn.setMaximumHeight(32)
        self.test_conn_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #56ab2f, stop:1 #a8e6cf);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                letter-spacing: 0.3px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6bc03e, stop:1 #b8f0df);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(86, 171, 47, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a932a, stop:1 #98d6bf);
                transform: translateY(0px);
            }
        """)
        self.test_conn_btn.clicked.connect(self.test_connections)
        self.test_conn_btn.clicked.connect(lambda: self.animate_button_click(self.test_conn_btn))

        conn_layout.addWidget(self.server_status_label)
        conn_layout.addWidget(self.local_status_label)
        conn_layout.addWidget(self.test_conn_btn)

        # Table selection with modern styling
        table_group = QGroupBox("📋 Select Tables to Sync")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(8)

        # Search input in its own row
        self.table_search_input = QLineEdit()
        self.table_search_input.setPlaceholderText("🔍 Search tables...")
        self.table_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                background: rgba(255,255,255,0.05);
                color: #e8e9ea;
                font-size: 12px;
                font-weight: 500;
                max-height: 24px;
            }
            QLineEdit:focus {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.1);
            }
            QLineEdit:hover {
                border-color: rgba(255,255,255,0.2);
            }
        """)
        self.table_search_input.textChanged.connect(self.filter_tables)
        table_layout.addWidget(self.table_search_input)

        # Control buttons in compact horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMaximumHeight(28)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 6px 12px;
                min-width: 60px;
            }
        """)
        self.select_all_btn.clicked.connect(self.select_all_tables)
        self.select_all_btn.clicked.connect(lambda: self.animate_button_click(self.select_all_btn))

        self.discover_tables_btn = QPushButton("🔍 Discover")
        self.discover_tables_btn.setMaximumHeight(28)
        self.discover_tables_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 6px 12px;
                min-width: 60px;
            }
        """)
        self.discover_tables_btn.clicked.connect(self.discover_tables)
        self.discover_tables_btn.clicked.connect(lambda: self.animate_button_click(self.discover_tables_btn))

        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.discover_tables_btn)
        button_layout.addStretch()
        table_layout.addLayout(button_layout)

        # Tables container with compact ScrollArea
        self.table_checkboxes = {}
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(120)
        scroll_area.setMinimumHeight(80)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                background: rgba(255,255,255,0.02);
            }
        """)

        tables_widget = QWidget()
        self.tables_container = QVBoxLayout(tables_widget)
        self.tables_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tables_container.setSpacing(2)
        self.tables_container.setContentsMargins(4, 4, 4, 4)

        scroll_area.setWidget(tables_widget)
        table_layout.addWidget(scroll_area)

        # Add compact placeholder text
        self.no_tables_label = QLabel("Click '🔍 Discover' to load tables")
        self.no_tables_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_tables_label.setStyleSheet("""
            color: #95a5a6;
            font-style: italic;
            font-size: 11px;
            padding: 10px;
        """)
        self.tables_container.addWidget(self.no_tables_label)

        # Database Configuration group
        config_group = QGroupBox("⚙️ Database Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(4)

        self.config_db_btn = QPushButton("🔧 Configure Databases")
        self.config_db_btn.setMaximumHeight(32)
        self.config_db_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 12px;
                letter-spacing: 0.3px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c8ff4, stop:1 #8662c4);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a74d6, stop:1 #6a4499);
                transform: translateY(0px);
            }
        """)
        self.config_db_btn.clicked.connect(self.open_database_config)
        self.config_db_btn.clicked.connect(lambda: self.animate_button_click(self.config_db_btn))

        config_layout.addWidget(self.config_db_btn)

        # Sync Destination group
        dest_group = QGroupBox("🎯 Sync Destination")
        dest_layout = QVBoxLayout(dest_group)
        dest_layout.setSpacing(4)

        # Destination type selection
        self.destination_type = QComboBox()
        self.destination_type.addItems([
            "PostgreSQL → SQLite (Local)",
            "SQLite → PostgreSQL (Server)",
            "PostgreSQL → PostgreSQL (Server)"
        ])
        self.destination_type.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.1);
                border: 2px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: 500;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #667eea;
                background: rgba(102, 126, 234, 0.1);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: #2c3e50;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: #667eea;
            }
        """)
        self.destination_type.currentTextChanged.connect(self.on_destination_changed)

        dest_layout.addWidget(self.destination_type)

        # Status label for destination
        self.destination_status = QLabel("📊 Standard sync to SQLite local database")
        self.destination_status.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 11px;
                font-style: italic;
                padding: 5px;
                background-color: rgba(149, 165, 166, 0.1);
                border-radius: 4px;
            }
        """)
        self.destination_status.setWordWrap(True)
        dest_layout.addWidget(self.destination_status)

        # Sync controls with modern styling
        sync_group = QGroupBox("⚡ Sync Operations")
        sync_layout = QVBoxLayout(sync_group)

        self.server_to_local_btn = QPushButton("📥 Server → Local")
        self.server_to_local_btn.setMinimumWidth(140)
        self.server_to_local_btn.clicked.connect(lambda: self.start_sync('server_to_local'))
        self.server_to_local_btn.clicked.connect(lambda: self.animate_button_click(self.server_to_local_btn))
        self.server_to_local_btn.setProperty("class", "warning")

        self.local_to_server_btn = QPushButton("📤 Local → Server")
        self.local_to_server_btn.setMinimumWidth(140)
        self.local_to_server_btn.clicked.connect(lambda: self.start_sync('local_to_server'))
        self.local_to_server_btn.clicked.connect(lambda: self.animate_button_click(self.local_to_server_btn))
        self.local_to_server_btn.setProperty("class", "danger")

        # Progress section
        progress_layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Progress details label
        self.progress_details_label = QLabel("Ready to sync")
        self.progress_details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_details_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 11px;
                font-style: italic;
                padding: 5px;
            }
        """)
        self.progress_details_label.setVisible(False)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_details_label)

        sync_layout.addWidget(self.server_to_local_btn)
        sync_layout.addWidget(self.local_to_server_btn)
        sync_layout.addLayout(progress_layout)

        # Add all groups with proper spacing
        left_layout.addWidget(conn_group)
        left_layout.addWidget(config_group)
        left_layout.addWidget(dest_group)
        left_layout.addWidget(table_group)
        left_layout.addWidget(sync_group)

        # Add compact instruction at bottom
        instruction_label = QLabel("💡 Test → Configure → Discover → Select → Sync")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 9px;
                font-style: italic;
                padding: 4px;
                background-color: rgba(127, 140, 141, 0.1);
                border-radius: 3px;
                margin-top: 5px;
            }
        """)
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(instruction_label)

        left_layout.addStretch()

        return left_widget

    def create_right_panel(self):
        """Create right panel with logs and status"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)

        # Status display with modern styling
        status_group = QGroupBox("📊 Current Status")
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

        # Table information with modern styling
        info_group = QGroupBox("📈 Table Information")
        info_layout = QVBoxLayout(info_group)

        # Preview button
        preview_layout = QHBoxLayout()
        self.preview_differences_btn = QPushButton("👁️ Preview Differences")
        self.preview_differences_btn.clicked.connect(self.show_differences_preview)
        self.preview_differences_btn.clicked.connect(lambda: self.animate_button_click(self.preview_differences_btn))
        preview_layout.addWidget(self.preview_differences_btn)

        self.refresh_info_btn = QPushButton("🔄 Refresh Table Info")
        self.refresh_info_btn.clicked.connect(self.refresh_table_info)
        self.refresh_info_btn.clicked.connect(lambda: self.animate_button_click(self.refresh_info_btn))
        preview_layout.addWidget(self.refresh_info_btn)
        info_layout.addLayout(preview_layout)

        # Table with scroll area for better responsiveness
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setMinimumHeight(180)
        table_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #34495e;
                border-radius: 6px;
                background-color: #34495e;
            }
            QScrollArea QWidget {
                background-color: #34495e;
            }
        """)

        self.info_table = QTableWidget()
        self.info_table.setColumnCount(4)
        self.info_table.setHorizontalHeaderLabels(["Table Name", "Server Rows", "Local Rows", "Difference"])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.info_table.setMinimumHeight(200)
        self.info_table.itemSelectionChanged.connect(self.update_selection_icons)

        table_scroll.setWidget(self.info_table)
        info_layout.addWidget(table_scroll)

        # Log display with modern styling
        log_group = QGroupBox("📝 Sync Logs")
        log_layout = QVBoxLayout(log_group)

        # Log display with scroll area
        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        log_scroll.setMinimumHeight(150)
        log_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #34495e;
                border-radius: 6px;
                background-color: #34495e;
            }
        """)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Sync logs will appear here...")
        log_scroll.setWidget(self.log_text)
        log_layout.addWidget(log_scroll)

        self.clear_log_btn = QPushButton("🗑️ Clear Logs")
        self.clear_log_btn.clicked.connect(self.clear_logs)
        self.clear_log_btn.clicked.connect(lambda: self.animate_button_click(self.clear_log_btn))
        log_layout.addWidget(self.clear_log_btn)

        right_layout.addWidget(status_group)
        right_layout.addWidget(info_group)
        right_layout.addWidget(log_group)

        return right_widget

    def on_destination_changed(self, destination_text):
        """Handle destination type change"""
        if "PostgreSQL → SQLite" in destination_text:
            self.destination_status.setText("📊 Standard sync from PostgreSQL server to local SQLite database")
            self.server_to_local_btn.setText("📥 Server → Local (SQLite)")
            self.local_to_server_btn.setText("📤 Local (SQLite) → Server")

        elif "SQLite → PostgreSQL" in destination_text:
            self.destination_status.setText("📤 Upload sync from local SQLite to PostgreSQL server")
            self.server_to_local_btn.setText("📥 Server → Local (SQLite)")
            self.local_to_server_btn.setText("📤 Local (SQLite) → Server")

        elif "PostgreSQL → PostgreSQL" in destination_text:
            self.destination_status.setText("🔄 Advanced sync between two PostgreSQL servers. Configure target server in Database Configuration.")
            self.server_to_local_btn.setText("📥 Source Server → Target Server")
            self.local_to_server_btn.setText("📤 Target Server → Source Server")

        self.log(f"Sync destination changed to: {destination_text}")

        # Update database connections and table info when destination changes
        self.update_connection_labels_for_destination()
        self.refresh_table_info_for_destination()

    def get_current_sync_mode(self):
        """Get current sync mode based on destination selection"""
        dest_text = self.destination_type.currentText()
        if "PostgreSQL → PostgreSQL" in dest_text:
            return "postgresql_to_postgresql"
        elif "SQLite → PostgreSQL" in dest_text:
            return "sqlite_to_postgresql"
        else:
            return "postgresql_to_sqlite"

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

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # Test connections shortcut
        test_conn_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        test_conn_shortcut.activated.connect(self.test_connections)
        test_conn_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Test Connections"))

        # Discover tables shortcut
        discover_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        discover_shortcut.activated.connect(self.discover_tables)
        discover_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Discover Tables"))

        # Refresh table info shortcut
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.refresh_table_info)
        refresh_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Refresh Table Info"))

        # Sync Server to Local shortcut
        sync_server_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        sync_server_shortcut.activated.connect(lambda: self.start_sync('server_to_local'))
        sync_server_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Sync Server → Local"))

        # Sync Local to Server shortcut
        sync_local_shortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        sync_local_shortcut.activated.connect(lambda: self.start_sync('local_to_server'))
        sync_local_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Sync Local → Server"))

        # Clear logs shortcut
        clear_logs_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_logs_shortcut.activated.connect(self.clear_logs)
        clear_logs_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Clear Logs"))

        # Focus search box shortcut
        focus_search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        focus_search_shortcut.activated.connect(lambda: self.table_search_input.setFocus())
        focus_search_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Focus Search"))

        # Preview differences shortcut
        preview_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        preview_shortcut.activated.connect(self.show_differences_preview)
        preview_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Preview Differences"))

        # Select all tables shortcut
        select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        select_all_shortcut.activated.connect(self.select_all_tables)

        # Escape key to close dialogs or exit fullscreen
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.handle_escape_key)

        # F11 key to toggle fullscreen
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        fullscreen_shortcut.activated.connect(lambda: self.log("⌨️ Keyboard shortcut: Toggle Fullscreen"))

        # Alt+Enter alternative for fullscreen
        fullscreen_alt_shortcut = QShortcut(QKeySequence("Alt+Return"), self)
        fullscreen_alt_shortcut.activated.connect(self.toggle_fullscreen)

        # Store shortcuts for cleanup if needed
        self.shortcuts = [
            test_conn_shortcut, discover_shortcut, refresh_shortcut,
            sync_server_shortcut, sync_local_shortcut, clear_logs_shortcut,
            focus_search_shortcut, preview_shortcut, select_all_shortcut,
            escape_shortcut, fullscreen_shortcut, fullscreen_alt_shortcut
        ]

    def close_active_dialogs(self):
        """Close any active dialogs"""
        # This method can be extended to close specific dialogs
        pass

    def handle_escape_key(self):
        """Handle escape key - exit fullscreen or close dialogs"""
        if self.isFullScreen():
            self.toggle_fullscreen()
            self.log("⌨️ Exited fullscreen mode")
        else:
            self.close_active_dialogs()

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self.isFullScreen():
            self.showNormal()
            self.log("🪟 Switched to windowed mode")
        else:
            self.showFullScreen()
            self.log("🖥️ Switched to fullscreen mode")

    def test_connections(self):
        """Test database connections and update UI."""
        self.log("Testing database connections...")
        results = self.db_manager.test_connections()

        # Get current destination type to set appropriate labels
        dest_text = self.destination_type.currentText()

        # Determine labels based on destination type
        if "PostgreSQL → PostgreSQL" in dest_text:
            server_label_prefix = "Source Server"
            local_label_prefix = "Target Server"
        elif "SQLite → PostgreSQL" in dest_text:
            server_label_prefix = "Server (PostgreSQL)"
            local_label_prefix = "Local (SQLite)"
        else:  # PostgreSQL → SQLite (default)
            server_label_prefix = "Server (PostgreSQL)"
            local_label_prefix = "Local (SQLite)"

        # Update server connection status
        if results['server']:
            self.server_status_label.setText(f"🟢 {server_label_prefix}: Connected")
            self.server_status_label.setStyleSheet("""
                color: #2ecc71;
                background-color: rgba(46, 204, 113, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 2px solid #2ecc71;
                font-weight: bold;
                font-size: 11px;
                transition: all 0.3s ease;
            """)
            # Add pulse animation
            pulse = self.add_pulse_effect(self.server_status_label)
            QTimer.singleShot(100, pulse)
        else:
            self.server_status_label.setText(f"🔴 {server_label_prefix}: Failed")
            self.server_status_label.setStyleSheet("""
                color: #e74c3c;
                background-color: rgba(231, 76, 60, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 2px solid #e74c3c;
                font-weight: bold;
                font-size: 11px;
                transition: all 0.3s ease;
            """)

        # Update local/target connection status
        if results['local']:
            self.local_status_label.setText(f"🟢 {local_label_prefix}: Connected")
            self.local_status_label.setStyleSheet("""
                color: #2ecc71;
                background-color: rgba(46, 204, 113, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 2px solid #2ecc71;
                font-weight: bold;
                font-size: 11px;
                transition: all 0.3s ease;
            """)
            # Add pulse animation
            pulse = self.add_pulse_effect(self.local_status_label)
            QTimer.singleShot(100, pulse)
        else:
            self.local_status_label.setText(f"🔴 {local_label_prefix}: Failed")
            self.local_status_label.setStyleSheet("""
                color: #e74c3c;
                background-color: rgba(231, 76, 60, 0.1);
                padding: 4px 8px;
                border-radius: 4px;
                border: 2px solid #e74c3c;
                font-weight: bold;
                font-size: 11px;
                transition: all 0.3s ease;
            """)
        return results

    def discover_tables(self):
        """Discover available tables from both databases"""
        self.update_status("Step 1: Testing connections...")
        QApplication.processEvents()

        # Test connections first
        results = self.test_connections()
        if not results['server'] or not results['local']:
            error_msg = "Database Connection Failed\n\n"
            if not results['server'] and not results['local']:
                error_msg += "❌ Both Server and Local databases failed to connect.\n\n"
            elif not results['server']:
                error_msg += "❌ Server database connection failed.\n"
                error_msg += "✅ Local database connected successfully.\n\n"
            else:
                error_msg += "✅ Server database connected successfully.\n"
                error_msg += "❌ Local database connection failed.\n\n"

            error_msg += "🔧 Troubleshooting steps:\n"
            error_msg += "1. Check your internet connection\n"
            error_msg += "2. Verify database credentials in database_config.py\n"
            error_msg += "3. Ensure PostgreSQL server is running\n"
            error_msg += "4. Check if local SQLite file exists\n"
            error_msg += "5. Try running 'Test Connections' again"

            QMessageBox.warning(self, "Connection Error", error_msg)
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
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-size: 11px;
                        color: #e8e9ea;
                        spacing: 6px;
                        padding: 2px;
                        font-weight: 500;
                    }
                    QCheckBox::indicator {
                        width: 14px;
                        height: 14px;
                    }
                """)
                self.table_checkboxes[table] = checkbox
                self.tables_container.addWidget(checkbox)
        else:
            # Show placeholder again if no tables
            self.no_tables_label.setText("No common tables found.")
            self.no_tables_label.setVisible(True)

    def filter_tables(self):
        """Filter table checkboxes based on search text"""
        search_text = self.table_search_input.text().lower()

        # Show/hide checkboxes based on search
        for table, checkbox in self.table_checkboxes.items():
            if search_text in table.lower():
                checkbox.setVisible(True)
            else:
                checkbox.setVisible(False)

        # Update select all button text based on visible checkboxes
        visible_checkboxes = [cb for cb in self.table_checkboxes.values() if cb.isVisible()]
        if visible_checkboxes:
            all_visible_checked = all(cb.isChecked() for cb in visible_checkboxes)
            self.select_all_btn.setText("Deselect All Visible" if all_visible_checked else "Select All Visible")
        else:
            self.select_all_btn.setText("Select / Deselect All")

    def select_all_tables(self):
        """Toggle select all visible tables"""
        if not self.table_checkboxes:
            QMessageBox.information(self, "Info", "Please discover tables first.")
            return

        # Get only visible checkboxes
        visible_checkboxes = [cb for cb in self.table_checkboxes.values() if cb.isVisible()]

        if not visible_checkboxes:
            QMessageBox.information(self, "Info", "No tables match your search criteria.")
            return

        all_visible_checked = all(cb.isChecked() for cb in visible_checkboxes)
        for checkbox in visible_checkboxes:
            checkbox.setChecked(not all_visible_checked)

        # Update button text
        self.select_all_btn.setText("Deselect All Visible" if not all_visible_checked else "Select All Visible")

    def get_selected_tables(self) -> list:
        """Get list of selected tables"""
        return [table for table, checkbox in self.table_checkboxes.items()
                if checkbox.isChecked()]

    def start_sync(self, direction: str):
        """Start sync operation"""
        selected_tables = self.get_selected_tables()

        if not selected_tables:
            QMessageBox.warning(self, "No Tables Selected",
                              "Please select at least one table to sync.\n\n"
                              "💡 Tip: Use 'Select All Visible' to select all filtered tables, "
                              "or use the search box to find specific tables.")
            return

        # Get current sync mode
        sync_mode = self.get_current_sync_mode()

        # Check if target server is configured for PostgreSQL to PostgreSQL sync
        if sync_mode == "postgresql_to_postgresql":
            if not (self.database_config and
                    self.database_config.get('target_server') and
                    self.database_config['target_server'].get('host')):
                QMessageBox.warning(self, "Target Server Not Configured",
                                  "PostgreSQL to PostgreSQL sync requires a target server to be configured.\n\n"
                                  "Please click '🔧 Configure Databases' and set up the Target PostgreSQL Server.")
                return

        # Build confirmation dialog based on sync mode
        if sync_mode == "postgresql_to_postgresql":
            if direction == 'server_to_local':
                direction_text = "Source Server → Target Server"
                target = "target server"
            else:
                direction_text = "Target Server → Source Server"
                target = "source server"
        elif sync_mode == "sqlite_to_postgresql":
            direction_text = "SQLite Local → PostgreSQL Server" if direction == 'local_to_server' else "PostgreSQL Server → SQLite Local"
            target = "server" if direction == 'local_to_server' else "local SQLite"
        else:  # postgresql_to_sqlite (default)
            direction_text = "PostgreSQL Server → SQLite Local" if direction == 'server_to_local' else "SQLite Local → PostgreSQL Server"
            target = "local SQLite" if direction == 'server_to_local' else "server"

        reply = QMessageBox.question(
            self,
            "Confirm Sync Operation",
            f"Are you sure you want to sync {direction_text}?\n\n"
            f"This will COMPLETELY CLEAR all data in the {target} database tables:\n"
            f"{', '.join(selected_tables)}\n\n"
            f"Sync Mode: {sync_mode.replace('_', ' ').title()}\n"
            f"This operation cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._execute_sync(direction, selected_tables, sync_mode)

    def _execute_sync(self, direction: str, selected_tables: list, sync_mode: str = "postgresql_to_sqlite"):
        """Execute the sync operation using safe multiprocessing"""
        # Disable buttons
        self.server_to_local_btn.setEnabled(False)
        self.local_to_server_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_details_label.setVisible(True)

        try:
            # Use SafeSyncWorker instead of QThread
            self.sync_worker = SafeSyncWorker(
                callback_progress=self.progress_bar.setValue,
                callback_status=self.update_status,
                callback_finished=self.sync_finished
            )

            # Apply current database configuration to sync worker
            if self.database_config:
                self.sync_worker.set_database_config(self.database_config)

            # Start sync in separate process with sync mode
            self.sync_worker.start_sync(selected_tables, direction, sync_mode)

            # Start timer to check for results from the multiprocessing worker
            self.sync_timer = QTimer()
            self.sync_timer.timeout.connect(self._check_sync_results)
            self.sync_timer.start(100)  # Check every 100ms

        except Exception as e:
            self.sync_finished(False, f"Failed to start sync: {str(e)}")

    def _check_sync_results(self):
        """Check for results from multiprocessing sync worker"""
        try:
            if self.sync_worker:
                # Check results returns False when sync is complete
                continue_checking = self.sync_worker.check_results()
                if not continue_checking:
                    # Sync is complete, stop the timer
                    if self.sync_timer:
                        self.sync_timer.stop()
                        self.sync_timer = None
        except Exception as e:
            self.log(f"Error checking sync results: {e}")
            if self.sync_timer:
                self.sync_timer.stop()
                self.sync_timer = None

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)
        self.log(message)

    def update_progress_details(self, message: str):
        """Update progress details label"""
        self.progress_details_label.setText(message)
        self.progress_details_label.setVisible(True)

    def create_button_animation(self, button: QPushButton, property_name: str, start_value: int, end_value: int, duration: int = 300):
        """Create animation for button properties"""
        animation = QPropertyAnimation(button, QByteArray(property_name.encode()))
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    def animate_button_click(self, button: QPushButton):
        """Enhanced button click animation with modern effects"""
        # Create animation group for simultaneous effects
        self.animation_group = QParallelAnimationGroup()

        # Scale animation
        scale_animation = QPropertyAnimation(button, b"geometry")
        scale_animation.setDuration(200)
        current_rect = button.geometry()

        # Slightly shrink the button
        shrunk_rect = QRect(
            current_rect.x() + 2,
            current_rect.y() + 2,
            current_rect.width() - 4,
            current_rect.height() - 4
        )

        scale_animation.setStartValue(current_rect)
        scale_animation.setEndValue(shrunk_rect)
        scale_animation.setEasingCurve(QEasingCurve.Type.OutQuart)

        self.animation_group.addAnimation(scale_animation)
        self.animation_group.start()

        # Restore animation after delay
        QTimer.singleShot(150, lambda: self.animate_button_restore(button, current_rect))

    def animate_button_restore(self, button: QPushButton, original_rect):
        """Restore button to original size with bounce effect"""
        restore_animation = QPropertyAnimation(button, b"geometry")
        restore_animation.setDuration(250)
        restore_animation.setStartValue(button.geometry())
        restore_animation.setEndValue(original_rect)
        restore_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        restore_animation.start()

    def create_fade_animation(self, widget, start_opacity: float, end_opacity: float, duration: int = 500):
        """Create fade in/out animation"""
        effect = widget.graphicsEffect()
        if not effect:
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        return animation

    def create_slide_animation(self, widget, start_pos, end_pos, duration: int = 400):
        """Create sliding animation"""
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    def add_pulse_effect(self, widget):
        """Enhanced pulse effect with modern styling"""
        original_style = widget.styleSheet()

        def pulse():
            # Modern pulse effect with gradient glow
            pulse_style = original_style + """
                border: 2px solid #667eea;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.3), stop:1 rgba(118, 75, 162, 0.3));
                box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
            """
            widget.setStyleSheet(pulse_style)

            # Create pulsing animation
            self.pulse_animation = QPropertyAnimation(widget, b"geometry")
            self.pulse_animation.setDuration(300)
            current_rect = widget.geometry()
            expanded_rect = QRect(
                current_rect.x() - 2,
                current_rect.y() - 2,
                current_rect.width() + 4,
                current_rect.height() + 4
            )
            self.pulse_animation.setStartValue(current_rect)
            self.pulse_animation.setEndValue(expanded_rect)
            self.pulse_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.pulse_animation.start()

            # Restore after animation
            QTimer.singleShot(400, lambda: self.restore_from_pulse(widget, original_style, current_rect))

        return pulse

    def restore_from_pulse(self, widget, original_style, original_rect):
        """Restore widget from pulse effect"""
        widget.setStyleSheet(original_style)
        restore_animation = QPropertyAnimation(widget, b"geometry")
        restore_animation.setDuration(200)
        restore_animation.setStartValue(widget.geometry())
        restore_animation.setEndValue(original_rect)
        restore_animation.setEasingCurve(QEasingCurve.Type.InQuad)
        restore_animation.start()

    def show_loading_indicator(self, widget, message="Loading..."):
        """Show modern loading indicator"""
        from PyQt6.QtWidgets import QGraphicsOpacityEffect

        # Create loading overlay
        self.loading_widget = QWidget(widget)
        self.loading_widget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.7);
                border-radius: 12px;
            }
            QLabel {
                color: #e8e9ea;
                font-size: 14px;
                font-weight: 600;
            }
        """)

        layout = QVBoxLayout(self.loading_widget)
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.loading_widget.setGeometry(widget.rect())
        self.loading_widget.show()

        # Fade in animation
        fade_in = self.create_fade_animation(self.loading_widget, 0.0, 1.0, 300)
        fade_in.start()

    def hide_loading_indicator(self):
        """Hide loading indicator with fade out"""
        if hasattr(self, 'loading_widget'):
            fade_out = self.create_fade_animation(self.loading_widget, 1.0, 0.0, 200)
            fade_out.finished.connect(lambda: self.loading_widget.deleteLater())
            fade_out.start()

    def sync_finished(self, success: bool, message: str):
        """Handle sync completion"""
        # Re-enable buttons
        self.server_to_local_btn.setEnabled(True)
        self.local_to_server_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_details_label.setVisible(False)

        if success:
            self.status_label.setText("✅ Sync completed successfully")
            self.progress_details_label.setText("Sync completed successfully")
            QMessageBox.information(self, "Sync Successful",
                                  f"🎉 {message}\n\n"
                                  "The synchronization has been completed successfully. "
                                  "You can now check the updated data in your databases.")
        else:
            self.status_label.setText("❌ Sync failed")
            self.progress_details_label.setText("Sync failed - check logs for details")

            # Enhanced error message with suggestions
            error_msg = f"Sync Operation Failed\n\n{message}\n\n"
            error_msg += "🔧 Possible solutions:\n"
            error_msg += "• Check your internet connection\n"
            error_msg += "• Verify database permissions\n"
            error_msg += "• Ensure sufficient disk space\n"
            error_msg += "• Check database server status\n"
            error_msg += "• Review the logs for detailed error information\n\n"
            error_msg += "💡 You can try again or contact support if the issue persists."

            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("Sync Error")
            error_dialog.setText(error_msg)
            error_dialog.setStandardButtons(QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel)

            if error_dialog.exec() == QMessageBox.StandardButton.Retry:
                # Re-enable buttons and allow retry
                self.server_to_local_btn.setEnabled(True)
                self.local_to_server_btn.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.progress_details_label.setVisible(False)
                self.update_status("Ready for retry")

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

            # Calculate difference
            difference = server_count - local_count
            if difference > 0:
                diff_text = f"+{difference}"
                diff_color = "#27ae60"  # Green for more in server
            elif difference < 0:
                diff_text = f"{difference}"
                diff_color = "#e74c3c"  # Red for more in local
            else:
                diff_text = "0"
                diff_color = "#95a5a6"  # Gray for no difference

            item_diff = QTableWidgetItem(diff_text)
            item_diff.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_diff.setForeground(QColor(diff_color))

            # Center align count columns
            item_server.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_local.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.info_table.setItem(i, 0, item_table)
            self.info_table.setItem(i, 1, item_server)
            self.info_table.setItem(i, 2, item_local)
            self.info_table.setItem(i, 3, item_diff)

            # Color code rows based on count differences
            highlight_color = QColor("#574B2B") # Dark yellow for differences
            transparent_color = QColor("transparent")

            if server_count != local_count:
                for col in range(4):
                    self.info_table.item(i, col).setBackground(highlight_color)
            else:
                for col in range(4):
                    self.info_table.item(i, col).setBackground(transparent_color)

    def show_differences_preview(self):
        """Show preview of differences between server and local databases"""
        if not self.available_tables:
            QMessageBox.information(self, "No Tables Available",
                                  "Please discover tables first to see differences preview.\n\n"
                                  "💡 Click '🔍 Discover Tables' to load available tables from both databases.")
            return

        results = self.db_manager.test_connections()
        if not results['server'] or not results['local']:
            error_msg = "Cannot show differences preview.\n\n"
            if not results['server'] and not results['local']:
                error_msg += "❌ Both databases are not connected.\n"
            elif not results['server']:
                error_msg += "❌ Server database is not connected.\n"
            else:
                error_msg += "❌ Local database is not connected.\n"

            error_msg += "\n🔧 Please test connections first by clicking '🔌 Test Connections'."
            QMessageBox.warning(self, "Connection Required", error_msg)
            return

        # Create preview dialog
        preview_dialog = QMessageBox(self)
        preview_dialog.setWindowTitle("Database Differences Preview")
        preview_dialog.setIcon(QMessageBox.Icon.Information)
        preview_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Build preview message
        preview_text = "📊 Database Differences Summary:\n\n"

        total_server_rows = 0
        total_local_rows = 0
        tables_with_differences = 0

        for table in self.available_tables:
            server_count = self.db_manager.get_table_count(table, from_server=True)
            local_count = self.db_manager.get_table_count(table, from_server=False)

            total_server_rows += server_count
            total_local_rows += local_count

            if server_count != local_count:
                tables_with_differences += 1
                diff = server_count - local_count
                preview_text += f"• {table}: Server={server_count}, Local={local_count} ({'+' if diff > 0 else ''}{diff})\n"

        preview_text += f"\n📈 Totals:\n"
        preview_text += f"• Server: {total_server_rows} total rows\n"
        preview_text += f"• Local: {total_local_rows} total rows\n"
        preview_text += f"• Tables with differences: {tables_with_differences}/{len(self.available_tables)}\n"

        if tables_with_differences == 0:
            preview_text += "\n✅ All tables are synchronized!"
        else:
            preview_text += f"\n⚠️ {tables_with_differences} table(s) have differences."

        preview_dialog.setText(preview_text)
        preview_dialog.exec()

    def clear_logs(self):
        """Clear log display"""
        self.log_text.clear()

    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.ensureCursorVisible()

    def apply_database_config(self, config):
        """Apply database configuration to DatabaseManager"""
        self.database_config = config

        # Apply server config
        if config['server']:
            self.db_manager.server_config = config['server']

        # Apply local config
        if config['local']:
            self.db_manager.local_config = config['local']

        # Apply target server config
        if config['target_server'] and config['target_server']['host']:
            self.db_manager.target_server_config = config['target_server']

        self.log(f"Database configuration applied successfully")

        # Update UI when configuration changes
        self.update_connection_labels_for_destination()
        self.refresh_table_info_for_destination()

    def update_connection_labels_for_destination(self):
        """Update connection status labels based on current destination"""
        dest_text = self.destination_type.currentText()

        # Determine labels based on destination type (matching test_connections logic)
        if "PostgreSQL → PostgreSQL" in dest_text:
            server_label_prefix = "Source Server"
            local_label_prefix = "Target Server"
        elif "SQLite → PostgreSQL" in dest_text:
            server_label_prefix = "Server (PostgreSQL)"
            local_label_prefix = "Local (SQLite)"
        else:  # PostgreSQL → SQLite (default)
            server_label_prefix = "Server (PostgreSQL)"
            local_label_prefix = "Local (SQLite)"

        # Update labels
        self.server_status_label.setText(f"⚪ {server_label_prefix}: Not tested")
        self.local_status_label.setText(f"⚪ {local_label_prefix}: Not tested")

        # Reset status styles
        default_style = """
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.1);
        """
        self.server_status_label.setStyleSheet(default_style)
        self.local_status_label.setStyleSheet(default_style)

    def refresh_table_info_for_destination(self):
        """Refresh table information when destination changes"""
        # Clear current table info
        self.info_table.setRowCount(0)

        # Clear available tables if destination changed significantly
        dest_text = self.destination_type.currentText()
        if "PostgreSQL → PostgreSQL" in dest_text:
            # For PostgreSQL to PostgreSQL, we need different table discovery
            self.available_tables = []
            self.update_table_checkboxes()
            self.log("Destination changed to PostgreSQL → PostgreSQL. Please test connections and discover tables again.")
        else:
            # For SQLite involved syncs, refresh if we have existing tables
            if self.available_tables:
                self.refresh_table_info()

    def open_database_config(self):
        """Open database configuration dialog"""
        dialog = DatabaseConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.apply_database_config(config)

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