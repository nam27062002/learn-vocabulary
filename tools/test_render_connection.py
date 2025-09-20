#!/usr/bin/env python3
"""
Test connection to Render.com PostgreSQL target server
"""
import psycopg2
import logging

def test_render_connection():
    """Test connection to the default target server"""

    # Default target server configuration
    target_config = {
        'host': 'dpg-d32033juibrs739dn540-a.oregon-postgres.render.com',
        'port': 5432,
        'database': 'learn_english_db_wuep',
        'user': 'learn_english_db_wuep_user',
        'password': 'RSZefSFspMPlsqz5MnxJeeUkKueWjSLH'
    }

    print("Testing connection to Render.com PostgreSQL target server...")
    print(f"Host: {target_config['host']}")
    print(f"Database: {target_config['database']}")
    print(f"User: {target_config['user']}")
    print()

    try:
        # Attempt connection
        print("Connecting...")
        conn = psycopg2.connect(
            host=target_config['host'],
            database=target_config['database'],
            user=target_config['user'],
            password=target_config['password'],
            port=target_config['port'],
            connect_timeout=10,
            sslmode='require'  # Render.com requires SSL
        )

        print("SUCCESS: Connection successful!")

        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL Version: {version}")

        # List available tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"Available tables ({len(tables)}):")
            for table in tables[:10]:  # Show first 10 tables
                print(f"   - {table[0]}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more tables")
        else:
            print("No tables found in public schema")

        # Close connection
        cursor.close()
        conn.close()
        print("Connection closed successfully")

        print()
        print("SUCCESS: Target server is ready for PostgreSQL->PostgreSQL sync!")
        return True

    except psycopg2.OperationalError as e:
        print(f"ERROR: Connection failed: {e}")
        print()
        print("Troubleshooting tips:")
        print("   - Check internet connection")
        print("   - Verify server credentials")
        print("   - Ensure firewall allows PostgreSQL connections")
        return False

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_render_connection()