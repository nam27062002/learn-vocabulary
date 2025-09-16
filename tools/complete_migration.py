#!/usr/bin/env python
"""
Complete Database Migration Tool
1. Sets up the new database schema
2. Migrates all data from old to new database
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        return False

def main():
    print("=== Complete Database Migration Process ===")
    print("This will:")
    print("1. Setup the new database schema")
    print("2. Migrate all data from old to new database")
    print()
    
    # Get confirmation
    confirm = input("Do you want to continue? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("Migration cancelled.")
        return False
    
    # Step 1: Setup new database
    if not run_command("python tools/setup_new_db.py", "Setting up new database schema"):
        return False
    
    # Step 2: Migrate data
    if not run_command("python tools/migrate_database.py", "Migrating data"):
        return False
    
    print("\n=== Migration Process Complete ===")
    print("[OK] Database migration completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)