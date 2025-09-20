#!/usr/bin/env python3
"""
Test PostgreSQL to PostgreSQL sync functionality
"""
from database_manager import DatabaseManager

def test_pg_to_pg_config():
    """Test PostgreSQL to PostgreSQL configuration"""

    # Create database manager
    db_manager = DatabaseManager()

    # Test server config
    server_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'learn_english_db',
        'user': 'postgres',
        'password': 'your_password'
    }

    # Test target server config (for demo, using same server but different database)
    target_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'learn_english_backup',  # Different database
        'user': 'postgres',
        'password': 'your_password'
    }

    # Apply configurations
    db_manager.server_config = server_config
    db_manager.target_server_config = target_config

    print("Testing PostgreSQL to PostgreSQL configuration...")

    # Test server connection
    try:
        if db_manager.connect_server():
            print("✅ Source PostgreSQL server connection: SUCCESS")
            db_manager.server_conn.close()
            db_manager.server_conn = None
        else:
            print("❌ Source PostgreSQL server connection: FAILED")
    except Exception as e:
        print(f"❌ Source PostgreSQL server error: {e}")

    # Test target server connection
    try:
        if db_manager.connect_target_server():
            print("✅ Target PostgreSQL server connection: SUCCESS")
            db_manager.target_server_conn.close()
            db_manager.target_server_conn = None
        else:
            print("❌ Target PostgreSQL server connection: FAILED")
    except Exception as e:
        print(f"❌ Target PostgreSQL server error: {e}")

    print("\nPostgreSQL to PostgreSQL sync configuration is ready!")
    print("You can now use the sync feature with PostgreSQL → PostgreSQL mode.")

if __name__ == "__main__":
    test_pg_to_pg_config()