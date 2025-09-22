#!/usr/bin/env python3
"""
Quick launcher for Database Migration GUI Tool

This script provides an easy way to start the GUI migration tool.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Import and run the GUI
try:
    from tools.migrate_database.gui_migrator import main
    main()
except ImportError as e:
    print(f"Error importing GUI migrator: {e}")
    print(f"Make sure you're running from the project root: {project_root}")
    print("And that all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)