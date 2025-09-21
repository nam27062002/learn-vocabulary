"""
Standalone sync worker to avoid Qt threading issues
"""
import sys
import os
import multiprocessing
import json
import traceback
from typing import List, Dict, Any
from database_manager import DatabaseManager
import logging

def sync_tables_process(tables: List[str], direction: str, result_queue, sync_mode: str = "postgresql_to_sqlite", db_config: Dict = None):
    """
    Standalone process for syncing tables
    This runs in a separate process to avoid memory corruption
    """
    try:
        # Setup logging for this process
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info(f"Starting sync process: {direction}, mode: {sync_mode}, tables: {tables}")

        db_manager = DatabaseManager()

        # Apply database configuration if provided
        if db_config:
            if db_config.get('server'):
                db_manager.server_config = db_config['server']
            if db_config.get('local'):
                db_manager.local_config = db_config['local']
            if db_config.get('target_server'):
                db_manager.target_server_config = db_config['target_server']

        # Sort tables by dependency order for foreign key safety
        sorted_tables = sort_tables_by_dependency(tables, sync_mode, direction)
        total_tables = len(sorted_tables)

        for i, table in enumerate(sorted_tables):
            try:
                result_queue.put({
                    'type': 'progress',
                    'table': table,
                    'current': i + 1,
                    'total': total_tables,
                    'message': f"Processing table {i+1} of {total_tables}: {table}"
                })

                if sync_mode == "postgresql_to_postgresql":
                    if direction == 'server_to_local':
                        success = _sync_table_server_to_target_server(db_manager, table)
                    else:
                        success = _sync_table_target_server_to_server(db_manager, table)
                elif sync_mode == "sqlite_to_postgresql":
                    if direction == 'local_to_server':
                        success = _sync_table_local_to_server(db_manager, table)
                    else:
                        success = _sync_table_server_to_local(db_manager, table)
                else:  # postgresql_to_sqlite (default)
                    if direction == 'server_to_local':
                        success = _sync_table_server_to_local(db_manager, table)
                    else:
                        success = _sync_table_local_to_server(db_manager, table)

                if not success:
                    result_queue.put({
                        'type': 'error',
                        'table': table,
                        'message': f"Failed to sync table: {table}"
                    })
                    continue

                # Send progress update
                progress = int(((i + 1) / total_tables) * 100)
                result_queue.put({
                    'type': 'progress_percent',
                    'progress': progress
                })

            except Exception as e:
                logger.error(f"Error syncing table {table}: {e}")
                result_queue.put({
                    'type': 'error',
                    'table': table,
                    'message': f"Error syncing {table}: {str(e)}"
                })
                continue

        # Final success message
        result_queue.put({
            'type': 'success',
            'message': f"Successfully synced {total_tables} tables"
        })

    except Exception as e:
        result_queue.put({
            'type': 'fatal_error',
            'message': f"Fatal sync error: {str(e)}\n{traceback.format_exc()}"
        })
    finally:
        try:
            db_manager.close_connections()
        except:
            pass

def sort_tables_by_dependency(tables: List[str], sync_mode: str, direction: str) -> List[str]:
    """Sort tables by dependency order to avoid foreign key constraint violations"""
    # Define dependency order (parent tables first for deletion, child tables first for insertion)
    # This is the order for DELETION (sync direction matters for order)

    deletion_order = [
        # Level 1: Most dependent tables (no other tables depend on them)
        'vocabulary_studysessionanswer',
        'vocabulary_studysession_decks_studied',
        'vocabulary_incorrectwordreview',
        'vocabulary_favoriteflashcard',
        'vocabulary_blacklistflashcard',
        'vocabulary_definition',
        'vocabulary_dailystatistics',
        'vocabulary_weeklystatistics',

        # Level 2: Tables that depend on flashcard/deck but have dependencies themselves
        'vocabulary_flashcard',
        'vocabulary_studysession',

        # Level 3: Tables that many others depend on
        'vocabulary_deck',

        # Level 4: Auth and account related (child first)
        'socialaccount_socialtoken',
        'socialaccount_socialapp_sites',
        'socialaccount_socialaccount',
        'socialaccount_socialapp',
        'account_emailconfirmation',
        'account_emailaddress',
        'accounts_customuser_user_permissions',
        'accounts_customuser_groups',

        # Level 5: User table (many dependencies)
        'accounts_customuser',

        # Level 6: Django framework tables
        'django_admin_log',
        'django_session',
        'cache_table',
        'auth_group_permissions',
        'auth_user_groups',
        'auth_user_user_permissions',
        'auth_group',

        # Level 7: Permission system
        'auth_permission',

        # Level 8: Core system tables (highest dependency)
        'django_content_type',
        'django_migrations',
        'django_site',
    ]

    # For insertion, we need reverse order (parent tables first)
    insertion_order = list(reversed(deletion_order))

    # Determine which order to use based on operation
    # Clear operations need deletion order, insert operations need insertion order
    use_insertion_order = (
        (direction == 'server_to_local' and sync_mode != 'sqlite_to_postgresql') or
        (direction == 'local_to_server' and sync_mode == 'sqlite_to_postgresql')
    )

    target_order = insertion_order if use_insertion_order else deletion_order

    # Sort tables according to the target order
    sorted_tables = []

    # Add tables in the defined order if they exist in the input
    for table in target_order:
        if table in tables:
            sorted_tables.append(table)

    # Add any remaining tables that weren't in our predefined order
    remaining_tables = [table for table in tables if table not in sorted_tables]
    sorted_tables.extend(sorted(remaining_tables))  # Sort remaining alphabetically

    return sorted_tables


def _sync_table_server_to_local(db_manager: DatabaseManager, table: str) -> bool:
    """Sync single table from server to local"""
    try:
        # Clear local table
        if not db_manager.clear_table(table, target_server=False):
            return False

        # Get data from server
        data = db_manager.get_table_data(table, from_server=True)
        if not data:
            return True  # Empty table is OK

        # Clean and insert data
        cleaned_data = db_manager.validate_and_clean_data(table, data)
        if not cleaned_data:
            return True  # No valid data is OK

        return db_manager.insert_data(table, cleaned_data, target_server=False)

    except Exception as e:
        logging.error(f"Error syncing table {table}: {e}")
        return False

def _sync_table_server_to_local(db_manager: DatabaseManager, table: str) -> bool:
    """Sync single table from server to local"""
    try:
        # Clear local table
        if not db_manager.clear_table(table, target_server=False):
            return False

        # Get data from server
        data = db_manager.get_table_data(table, from_server=True)
        if not data:
            return True  # Empty table is OK

        # Clean and insert data
        cleaned_data = db_manager.validate_and_clean_data(table, data)
        if not cleaned_data:
            return True  # No valid data is OK

        return db_manager.insert_data(table, cleaned_data, target_server=False)

    except Exception as e:
        logging.error(f"Error syncing table {table}: {e}")
        return False

def _sync_table_local_to_server(db_manager: DatabaseManager, table: str) -> bool:
    """Sync single table from local to server"""
    try:
        # Clear server table
        if not db_manager.clear_table(table, target_server=True):
            return False

        # Get data from local
        data = db_manager.get_table_data(table, from_server=False)
        if not data:
            return True  # Empty table is OK

        return db_manager.insert_data(table, data, target_server=True)

    except Exception as e:
        logging.error(f"Error syncing table {table}: {e}")
        return False

def _sync_table_server_to_target_server(db_manager: DatabaseManager, table: str) -> bool:
    """Sync single table from source server to target server (PostgreSQL to PostgreSQL)"""
    try:
        # Connect to both servers
        if not db_manager.connect_server():
            return False
        if not db_manager.connect_target_server():
            return False

        # Clear target server table
        target_cursor = db_manager.target_server_conn.cursor()
        target_cursor.execute(f"DELETE FROM {table}")
        db_manager.target_server_conn.commit()

        # Get data from source server
        source_cursor = db_manager.server_conn.cursor()
        source_cursor.execute(f"SELECT * FROM {table}")
        data = source_cursor.fetchall()

        if not data:
            return True  # Empty table is OK

        # Get column names
        column_names = [desc[0] for desc in source_cursor.description]

        # Insert data to target server in batches
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            placeholders = ','.join(['%s'] * len(column_names))
            insert_query = f"INSERT INTO {table} ({','.join(column_names)}) VALUES ({placeholders})"

            target_cursor.executemany(insert_query, batch)
            db_manager.target_server_conn.commit()

        logging.info(f"Successfully synced {len(data)} rows from source to target server for table {table}")
        return True

    except Exception as e:
        logging.error(f"Error syncing table {table} from server to target server: {e}")
        return False

def _sync_table_target_server_to_server(db_manager: DatabaseManager, table: str) -> bool:
    """Sync single table from target server to source server (PostgreSQL to PostgreSQL)"""
    try:
        # Connect to both servers
        if not db_manager.connect_server():
            return False
        if not db_manager.connect_target_server():
            return False

        # Clear source server table
        source_cursor = db_manager.server_conn.cursor()
        source_cursor.execute(f"DELETE FROM {table}")
        db_manager.server_conn.commit()

        # Get data from target server
        target_cursor = db_manager.target_server_conn.cursor()
        target_cursor.execute(f"SELECT * FROM {table}")
        data = target_cursor.fetchall()

        if not data:
            return True  # Empty table is OK

        # Get column names
        column_names = [desc[0] for desc in target_cursor.description]

        # Insert data to source server in batches
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            placeholders = ','.join(['%s'] * len(column_names))
            insert_query = f"INSERT INTO {table} ({','.join(column_names)}) VALUES ({placeholders})"

            source_cursor.executemany(insert_query, batch)
            db_manager.server_conn.commit()

        logging.info(f"Successfully synced {len(data)} rows from target to source server for table {table}")
        return True

    except Exception as e:
        logging.error(f"Error syncing table {table} from target server to server: {e}")
        return False

class SafeSyncWorker:
    """Safe sync worker using multiprocessing instead of threading"""

    def __init__(self, callback_progress=None, callback_status=None, callback_finished=None):
        self.callback_progress = callback_progress
        self.callback_status = callback_status
        self.callback_finished = callback_finished
        self.process = None
        self.result_queue = None
        self.database_config = None

    def set_database_config(self, config: Dict):
        """Set database configuration"""
        self.database_config = config

    def start_sync(self, tables: List[str], direction: str, sync_mode: str = "postgresql_to_sqlite"):
        """Start sync in separate process"""
        try:
            # Create multiprocessing queue for communication
            self.result_queue = multiprocessing.Queue()

            # Start sync process
            self.process = multiprocessing.Process(
                target=sync_tables_process,
                args=(tables, direction, self.result_queue, sync_mode, self.database_config),
                daemon=True  # Die when main process dies
            )
            self.process.start()

            # Start monitoring results
            self._monitor_results()

        except Exception as e:
            if self.callback_finished:
                self.callback_finished(False, f"Failed to start sync: {str(e)}")

    def _monitor_results(self):
        """Monitor results from sync process (called by QTimer)"""
        # This will be called by QTimer, not in a loop
        pass

    def check_results(self):
        """Check for new results (called by QTimer)"""
        try:
            if not self.process or not self.process.is_alive():
                # Process finished, check for any remaining messages
                while not self.result_queue.empty():
                    try:
                        result = self.result_queue.get_nowait()
                        self._handle_result(result)
                    except:
                        break

                # Process is done, stop checking
                return False

            # Check for new results
            try:
                result = self.result_queue.get_nowait()
                self._handle_result(result)
                return True  # Continue checking
            except:
                return True  # No new results, continue checking

        except Exception as e:
            if self.callback_finished:
                self.callback_finished(False, f"Error monitoring sync: {str(e)}")
            return False

    def _handle_result(self, result: Dict[str, Any]):
        """Handle result from sync process"""
        try:
            result_type = result.get('type')

            if result_type == 'progress':
                if self.callback_status:
                    self.callback_status(result.get('message', ''))

            elif result_type == 'progress_percent':
                if self.callback_progress:
                    self.callback_progress(result.get('progress', 0))

            elif result_type == 'error':
                if self.callback_status:
                    self.callback_status(f"Error: {result.get('message', '')}")

            elif result_type == 'success':
                if self.callback_finished:
                    self.callback_finished(True, result.get('message', 'Sync completed'))

            elif result_type == 'fatal_error':
                if self.callback_finished:
                    self.callback_finished(False, result.get('message', 'Fatal error'))

        except Exception as e:
            if self.callback_finished:
                self.callback_finished(False, f"Error handling result: {str(e)}")

    def stop(self):
        """Stop sync process"""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()