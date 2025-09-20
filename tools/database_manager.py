"""
Database Manager for handling connections and operations
"""
import sqlite3
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
import logging
from database_config import (
    SERVER_DB_CONFIG,
    LOCAL_DB_CONFIG,
    TABLES_TO_SYNC
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.server_conn = None
        self.local_conn = None

    def connect_server(self) -> bool:
        """Connect to PostgreSQL server"""
        try:
            self.server_conn = psycopg2.connect(
                host=SERVER_DB_CONFIG['HOST'],
                database=SERVER_DB_CONFIG['NAME'],
                user=SERVER_DB_CONFIG['USER'],
                password=SERVER_DB_CONFIG['PASSWORD'],
                port=SERVER_DB_CONFIG['PORT']
            )
            logger.info("Connected to PostgreSQL server successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL server: {e}")
            return False

    def connect_local(self) -> bool:
        """Connect to local SQLite database"""
        try:
            self.local_conn = sqlite3.connect(LOCAL_DB_CONFIG['NAME'])
            self.local_conn.row_factory = sqlite3.Row
            logger.info("Connected to local SQLite database successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local SQLite database: {e}")
            return False

    def test_connections(self) -> Dict[str, bool]:
        """Test both database connections"""
        server_ok = self.connect_server()
        local_ok = self.connect_local()

        if server_ok and self.server_conn:
            self.server_conn.close()
            self.server_conn = None
        if local_ok and self.local_conn:
            self.local_conn.close()
            self.local_conn = None

        return {
            'server': server_ok,
            'local': local_ok
        }

    def get_table_data(self, table_name: str, from_server: bool = True) -> List[Dict[str, Any]]:
        """Get all data from a specific table"""
        try:
            if from_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()

            cursor.execute(f"SELECT * FROM {table_name}")

            if from_server:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting data from table {table_name}: {e}")
            return []

    def get_table_structure(self, table_name: str, from_server: bool = True) -> List[str]:
        """Get table column structure"""
        try:
            if from_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor()
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")

            if from_server:
                columns = [row[0] for row in cursor.fetchall()]
            else:
                columns = [row[1] for row in cursor.fetchall()]

            return columns
        except Exception as e:
            logger.error(f"Error getting table structure for {table_name}: {e}")
            return []

    def clear_table(self, table_name: str, target_server: bool = True) -> bool:
        """Clear all data from a table"""
        try:
            if target_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor()
                cursor.execute(f"DELETE FROM {table_name}")
                self.server_conn.commit()
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()
                cursor.execute(f"DELETE FROM {table_name}")
                self.local_conn.commit()

            logger.info(f"Cleared table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing table {table_name}: {e}")
            return False

    def insert_data(self, table_name: str, data: List[Dict[str, Any]], target_server: bool = True) -> bool:
        """Insert data into a table"""
        if not data:
            return True

        try:
            if target_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor()

                # Build INSERT statement for PostgreSQL
                columns = list(data[0].keys())
                quoted_columns = [f'"{col}"' for col in columns]
                placeholders = ["%s"] * len(columns)
                query = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({', '.join(placeholders)})"

                for row in data:
                    values = [row.get(col) for col in columns]
                    cursor.execute(query, values)

                self.server_conn.commit()
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()

                # Build INSERT statement for SQLite
                columns = list(data[0].keys())
                quoted_columns = [f'"{col}"' for col in columns]
                placeholders = ["?"] * len(columns)
                query = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({', '.join(placeholders)})"

                for row in data:
                    values = [row.get(col) for col in columns]
                    cursor.execute(query, values)

                self.local_conn.commit()

            logger.info(f"Inserted {len(data)} rows into {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
            return False

    def get_table_count(self, table_name: str, from_server: bool = True) -> int:
        """Get row count from a table"""
        try:
            if from_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor()
                # Reset transaction if aborted
                try:
                    cursor.execute("SELECT 1")
                except:
                    self.server_conn.rollback()
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()

            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting count from table {table_name}: {e}")
            # Reset connection if transaction is aborted
            if from_server and "current transaction is aborted" in str(e).lower():
                try:
                    self.server_conn.rollback()
                except:
                    pass
            return 0

    def get_all_tables(self, from_server: bool = True) -> List[str]:
        """Get list of all tables in database"""
        try:
            if from_server:
                if not self.server_conn:
                    self.connect_server()
                cursor = self.server_conn.cursor()
                # PostgreSQL query to get all tables
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
            else:
                if not self.local_conn:
                    self.connect_local()
                cursor = self.local_conn.cursor()
                # SQLite query to get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                    AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]

            return tables
        except Exception as e:
            logger.error(f"Error getting tables list: {e}")
            return []

    def close_connections(self):
        """Close all database connections"""
        if self.server_conn:
            self.server_conn.close()
            self.server_conn = None
        if self.local_conn:
            self.local_conn.close()
            self.local_conn = None
        logger.info("All database connections closed")