"""
Database Manager for handling connections and operations
"""
import sqlite3
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
import logging
import json
import time
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
        self._connection_lock = None
        self._initialize_threading()

    def _initialize_threading(self):
        """Initialize thread safety"""
        try:
            import threading
            self._connection_lock = threading.Lock()
        except ImportError:
            self._connection_lock = None

    def connect_server(self) -> bool:
        """Connect to PostgreSQL server with thread safety"""
        if self._connection_lock:
            with self._connection_lock:
                return self._connect_server_unsafe()
        else:
            return self._connect_server_unsafe()

    def _connect_server_unsafe(self) -> bool:
        """Internal server connection method"""
        try:
            # Close existing connection if any
            if self.server_conn:
                try:
                    self.server_conn.close()
                except:
                    pass
                self.server_conn = None

            self.server_conn = psycopg2.connect(
                host=SERVER_DB_CONFIG['HOST'],
                database=SERVER_DB_CONFIG['NAME'],
                user=SERVER_DB_CONFIG['USER'],
                password=SERVER_DB_CONFIG['PASSWORD'],
                port=SERVER_DB_CONFIG['PORT'],
                connect_timeout=10  # Add timeout
            )
            logger.info("Connected to PostgreSQL server successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL server: {e}")
            self.server_conn = None
            return False

    def connect_local(self) -> bool:
        """Connect to local SQLite database with thread safety"""
        if self._connection_lock:
            with self._connection_lock:
                return self._connect_local_unsafe()
        else:
            return self._connect_local_unsafe()

    def _connect_local_unsafe(self) -> bool:
        """Internal local connection method"""
        try:
            # Close existing connection if any
            if self.local_conn:
                try:
                    self.local_conn.close()
                except:
                    pass
                self.local_conn = None

            self.local_conn = sqlite3.connect(
                LOCAL_DB_CONFIG['NAME'],
                timeout=10.0,  # Add timeout
                check_same_thread=False  # Allow multi-threading
            )
            self.local_conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self.local_conn.execute('PRAGMA journal_mode=WAL')
            logger.info("Connected to local SQLite database successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local SQLite database: {e}")
            self.local_conn = None
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

    def _convert_value_for_sqlite(self, value: Any) -> Any:
        """Convert PostgreSQL values to SQLite compatible types"""
        if value is None:
            return None
        elif isinstance(value, dict):
            # Convert dict to JSON string for SQLite
            return json.dumps(value, default=str)
        elif isinstance(value, list):
            # Convert list to JSON string for SQLite
            return json.dumps(value, default=str)
        elif isinstance(value, (bytes, bytearray)):
            # Convert bytes to string for SQLite
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 decoding fails, use base64 encoding
                import base64
                return base64.b64encode(value).decode('ascii')
        elif hasattr(value, 'isoformat'):
            # Convert datetime objects to ISO format string
            return value.isoformat()
        elif isinstance(value, bool):
            # Convert boolean to integer for SQLite
            return int(value)
        elif isinstance(value, (int, float, str)):
            # These types are directly supported
            return value
        elif isinstance(value, memoryview):
            # Convert memoryview to bytes then to string
            try:
                return value.tobytes().decode('utf-8')
            except UnicodeDecodeError:
                import base64
                return base64.b64encode(value.tobytes()).decode('ascii')
        else:
            # For any other type, convert to string
            try:
                # Try JSON serialization first for complex objects
                return json.dumps(value, default=str)
            except (TypeError, ValueError):
                try:
                    return str(value)
                except Exception:
                    logger.warning(f"Failed to convert value {value} of type {type(value)}, using None")
                    return None

    def insert_data(self, table_name: str, data: List[Dict[str, Any]], target_server: bool = True) -> bool:
        """Insert data into a table with improved type handling and batch processing"""
        if not data:
            return True

        try:
            if target_server:
                return self._insert_to_postgres(table_name, data)
            else:
                return self._insert_to_sqlite(table_name, data)
        except Exception as e:
            logger.error(f"Error inserting data into {table_name}: {e}")
            return False

    def _insert_to_postgres(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Insert data to PostgreSQL with batch processing"""
        if not self.server_conn:
            self.connect_server()

        cursor = self.server_conn.cursor()
        columns = list(data[0].keys())
        quoted_columns = [f'"{col}"' for col in columns]
        placeholders = ["%s"] * len(columns)
        query = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({', '.join(placeholders)})"

        # Process in batches of 100 rows
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                for row in batch:
                    values = [row.get(col) for col in columns]
                    cursor.execute(query, values)
                self.server_conn.commit()
                logger.debug(f"Inserted batch {i//batch_size + 1} ({len(batch)} rows) into {table_name}")
            except Exception as e:
                self.server_conn.rollback()
                logger.error(f"Error inserting batch {i//batch_size + 1} into {table_name}: {e}")
                raise

        logger.info(f"Inserted {len(data)} rows into {table_name}")
        return True

    def _insert_to_sqlite(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Insert data to SQLite with type conversion and error handling"""
        if not data:
            return True

        # Limit memory usage by processing in smaller chunks
        max_chunk_size = 100
        if len(data) > max_chunk_size:
            return self._insert_large_dataset(table_name, data, max_chunk_size)

        if not self.local_conn:
            self.connect_local()

        cursor = self.local_conn.cursor()
        columns = list(data[0].keys())
        quoted_columns = [f'"{col}"' for col in columns]
        placeholders = ["?"] * len(columns)
        query = f"INSERT INTO {table_name} ({', '.join(quoted_columns)}) VALUES ({', '.join(placeholders)})"

        # Special handling for problematic tables
        if table_name == 'socialaccount_socialaccount':
            return self._insert_socialaccount_data(cursor, query, columns, data)

        # Process row by row with detailed error handling
        successful_inserts = 0
        for i, row in enumerate(data):
            try:
                values = []
                for col in columns:
                    value = row.get(col)
                    converted_value = self._convert_value_for_sqlite(value)
                    values.append(converted_value)

                cursor.execute(query, values)
                successful_inserts += 1

                # Commit every 20 rows for better memory management
                if (i + 1) % 20 == 0:
                    self.local_conn.commit()
                    # Force garbage collection
                    import gc
                    gc.collect()

            except Exception as e:
                logger.error(f"Error inserting row {i+1} into {table_name}: {e}")
                logger.error(f"Problematic row data: {row}")

                # Skip this row and continue with others
                try:
                    self.local_conn.rollback()
                except:
                    pass
                continue

        # Final commit
        try:
            self.local_conn.commit()
        except Exception as e:
            logger.error(f"Error in final commit for {table_name}: {e}")

        if successful_inserts < len(data):
            logger.warning(f"Inserted {successful_inserts}/{len(data)} rows into {table_name}")
        else:
            logger.info(f"Inserted {successful_inserts} rows into {table_name}")

        return successful_inserts > 0

    def _insert_large_dataset(self, table_name: str, data: List[Dict[str, Any]], chunk_size: int) -> bool:
        """Handle large datasets by processing in chunks"""
        total_successful = 0
        total_rows = len(data)

        for i in range(0, total_rows, chunk_size):
            chunk = data[i:i + chunk_size]
            logger.info(f"Processing chunk {i//chunk_size + 1}/{(total_rows + chunk_size - 1)//chunk_size} for {table_name}")

            try:
                if self._insert_to_sqlite(table_name, chunk):
                    total_successful += len(chunk)

                # Force memory cleanup between chunks
                import gc
                gc.collect()
                time.sleep(0.1)  # Small delay to prevent overwhelming

            except Exception as e:
                logger.error(f"Error processing chunk {i//chunk_size + 1} for {table_name}: {e}")
                continue

        logger.info(f"Large dataset processing complete: {total_successful}/{total_rows} rows for {table_name}")
        return total_successful > 0

    def _insert_socialaccount_data(self, cursor, query: str, columns: List[str], data: List[Dict[str, Any]]) -> bool:
        """Special handler for socialaccount_socialaccount table"""
        successful_inserts = 0

        for i, row in enumerate(data):
            try:
                values = []
                for col in columns:
                    value = row.get(col)

                    # Special handling for known problematic fields
                    if col in ['extra_data', 'provider', 'uid']:
                        if value is None:
                            values.append(None)
                        elif col == 'extra_data' and isinstance(value, dict):
                            # Ensure extra_data is properly serialized
                            values.append(json.dumps(value, default=str, ensure_ascii=False))
                        elif isinstance(value, (str, int, float)):
                            values.append(value)
                        else:
                            # Convert other types to string
                            values.append(str(value))
                    else:
                        # Use standard conversion for other fields
                        converted_value = self._convert_value_for_sqlite(value)
                        values.append(converted_value)

                cursor.execute(query, values)
                successful_inserts += 1

            except Exception as e:
                logger.error(f"Error inserting socialaccount row {i+1}: {e}")
                logger.error(f"Row data: {row}")

                # Try to insert with minimal data (skip problematic fields)
                try:
                    minimal_values = []
                    for col in columns:
                        value = row.get(col)
                        if value is None or col in ['extra_data']:
                            minimal_values.append(None)
                        elif isinstance(value, (str, int, float, bool)):
                            minimal_values.append(value)
                        else:
                            minimal_values.append(str(value))

                    cursor.execute(query, minimal_values)
                    successful_inserts += 1
                    logger.info(f"Inserted socialaccount row {i+1} with minimal data")

                except Exception as e2:
                    logger.error(f"Failed to insert even minimal data for row {i+1}: {e2}")
                    continue

        # Final commit
        self.local_conn.commit()

        if successful_inserts > 0:
            logger.info(f"Inserted {successful_inserts}/{len(data)} socialaccount rows")
        else:
            logger.warning("No socialaccount rows were inserted successfully")

        return successful_inserts > 0

    def validate_and_clean_data(self, table_name: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean data before insertion"""
        if not data:
            return data

        cleaned_data = []
        for i, row in enumerate(data):
            try:
                cleaned_row = {}
                for key, value in row.items():
                    # Clean column names (remove quotes, spaces, etc.)
                    clean_key = str(key).strip().replace('"', '').replace("'", '')

                    # Convert value to SQLite compatible type
                    cleaned_value = self._convert_value_for_sqlite(value)
                    cleaned_row[clean_key] = cleaned_value

                cleaned_data.append(cleaned_row)
            except Exception as e:
                logger.warning(f"Skipping invalid row {i+1} in {table_name}: {e}")
                continue

        logger.info(f"Cleaned {len(cleaned_data)}/{len(data)} rows for {table_name}")
        return cleaned_data

    def test_table_sync(self, table_name: str) -> Dict[str, Any]:
        """Test sync capability for a specific table"""
        result = {
            'table_name': table_name,
            'server_accessible': False,
            'local_accessible': False,
            'data_compatible': False,
            'sample_row_count': 0,
            'errors': []
        }

        try:
            # Test server access
            server_data = self.get_table_data(table_name, from_server=True)
            result['server_accessible'] = True
            result['sample_row_count'] = len(server_data)

            # Test local access
            local_count = self.get_table_count(table_name, from_server=False)
            result['local_accessible'] = True

            # Test data compatibility if we have server data
            if server_data:
                cleaned_data = self.validate_and_clean_data(table_name, server_data[:1])
                result['data_compatible'] = len(cleaned_data) > 0

        except Exception as e:
            result['errors'].append(str(e))

        return result

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
        """Close all database connections safely"""
        if self._connection_lock:
            with self._connection_lock:
                self._close_connections_unsafe()
        else:
            self._close_connections_unsafe()

    def _close_connections_unsafe(self):
        """Internal connection closing method"""
        try:
            if self.server_conn:
                try:
                    self.server_conn.close()
                except Exception as e:
                    logger.warning(f"Error closing server connection: {e}")
                finally:
                    self.server_conn = None

            if self.local_conn:
                try:
                    self.local_conn.close()
                except Exception as e:
                    logger.warning(f"Error closing local connection: {e}")
                finally:
                    self.local_conn = None

            logger.info("All database connections closed")
        except Exception as e:
            logger.error(f"Error in close_connections: {e}")

    def __del__(self):
        """Destructor to ensure connections are closed"""
        try:
            self.close_connections()
        except:
            pass