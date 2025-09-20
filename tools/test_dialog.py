#!/usr/bin/env python3
"""
Test script for DatabaseConfigDialog
"""
import sys
from PyQt6.QtWidgets import QApplication
from sync_gui import DatabaseConfigDialog

def test_dialog():
    app = QApplication(sys.argv)

    # Create dialog
    dialog = DatabaseConfigDialog()

    # Show dialog
    result = dialog.exec()

    if result:
        config = dialog.get_config()
        print("Configuration:")
        print(f"Server: {config['server']}")
        print(f"Local: {config['local']}")
        print(f"Target Server: {config['target_server']}")
    else:
        print("Dialog cancelled")

if __name__ == "__main__":
    test_dialog()