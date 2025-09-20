#!/usr/bin/env python3
"""
Test DatabaseConfigDialog integration with main app
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from sync_gui import DatabaseConfigDialog

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Database Config")
        self.setGeometry(100, 100, 400, 200)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create test button
        test_btn = QPushButton("🔧 Test Database Config")
        test_btn.clicked.connect(self.test_config_dialog)
        layout.addWidget(test_btn)

    def test_config_dialog(self):
        """Test opening database config dialog"""
        try:
            print("Creating DatabaseConfigDialog...")
            dialog = DatabaseConfigDialog(self)
            print("Dialog created successfully!")

            print("Showing dialog...")
            result = dialog.exec()
            print(f"Dialog result: {result}")

            if result:
                config = dialog.get_config()
                print("Configuration retrieved successfully!")
            else:
                print("Dialog cancelled")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()