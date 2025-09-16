#!/usr/bin/env python
"""
Database Clearing Tool
Completely clears the target database before migration to ensure 100% data consistency
"""

import os
import sys
import django
import psycopg2
from psycopg2 import sql

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

class DatabaseCleaner:
    def __init__(self):
        # Target database configuration (current Django settings)
        from django.conf import settings
        db_settings = settings.DATABASES['default']
        self.db_config = {
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
            'database': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD']
        }

    def get_all_tables(self):
        """Get all tables in the database"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables

    def get_all_sequences(self):
        """Get all sequences in the database"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
            ORDER BY sequence_name;
        """)
        
        sequences = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return sequences

    def get_table_row_count(self, table_name):
        """Get row count for a table"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table_name)
            ))
            count = cursor.fetchone()[0]
        except:
            count = 0
        
        cursor.close()
        conn.close()
        
        return count

    def clear_all_data(self):
        """Clear all data from all tables"""
        print("=== Database Clearing Tool ===")
        print(f"Target: {self.db_config['database']} @ {self.db_config['host']}")
        print()
        
        # Get all tables
        tables = self.get_all_tables()
        print(f"Found {len(tables)} tables to clear")
        
        # Show current data summary
        total_rows = 0
        table_stats = {}
        for table in tables:
            count = self.get_table_row_count(table)
            table_stats[table] = count
            total_rows += count
            if count > 0:
                print(f"  {table}: {count} rows")
        
        print(f"\nTotal rows to delete: {total_rows}")
        
        if total_rows == 0:
            print("Database is already empty!")
            return True
        
        # Confirm clearing
        print("\n[WARNING] This will DELETE ALL DATA in the target database!")
        confirm = input("Are you sure you want to continue? (type 'DELETE ALL' to confirm): ")
        if confirm != 'DELETE ALL':
            print("Database clearing cancelled.")
            return False
        
        # Clear all tables
        print("\n=== Starting Database Clearing ===")
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        try:
            # Disable foreign key checks temporarily
            print("Disabling foreign key constraints...")
            cursor.execute("SET session_replication_role = replica;")
            
            cleared_tables = 0
            failed_tables = []
            
            for table in tables:
                if table_stats[table] > 0:
                    try:
                        print(f"Clearing {table}... ", end="")
                        cursor.execute(sql.SQL("DELETE FROM {}").format(
                            sql.Identifier(table)
                        ))
                        deleted_count = cursor.rowcount
                        print(f"[OK] Deleted {deleted_count} rows")
                        cleared_tables += 1
                    except Exception as e:
                        print(f"[ERROR] {e}")
                        failed_tables.append(table)
                else:
                    print(f"Skipping {table} (already empty)")
            
            # Reset sequences to 1
            print("\nResetting sequences...")
            sequences = self.get_all_sequences()
            for seq_name in sequences:
                try:
                    cursor.execute(sql.SQL("ALTER SEQUENCE {} RESTART WITH 1").format(
                        sql.Identifier(seq_name)
                    ))
                    print(f"  [OK] Reset {seq_name}")
                except Exception as e:
                    print(f"  [ERROR] Failed to reset {seq_name}: {e}")
            
            # Re-enable foreign key checks
            print("\nRe-enabling foreign key constraints...")
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            # Commit all changes
            conn.commit()
            
            # Summary
            print("\n=== Database Clearing Complete ===")
            if failed_tables:
                print(f"[WARNING] Failed to clear {len(failed_tables)} tables:")
                for table in failed_tables:
                    print(f"  - {table}")
            else:
                print("[OK] All tables cleared successfully!")
            
            print(f"Tables processed: {len(tables)}")
            print(f"Successfully cleared: {cleared_tables}")
            print(f"Failed: {len(failed_tables)}")
            print(f"Total rows deleted: {total_rows}")
            
            return len(failed_tables) == 0
            
        except Exception as e:
            print(f"\n[ERROR] Database clearing failed: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def verify_empty_database(self):
        """Verify that the database is completely empty"""
        print("\n=== Verifying Empty Database ===")
        
        tables = self.get_all_tables()
        total_rows = 0
        non_empty_tables = []
        
        for table in tables:
            count = self.get_table_row_count(table)
            total_rows += count
            if count > 0:
                non_empty_tables.append(f"{table}: {count} rows")
        
        if total_rows == 0:
            print("[OK] Database is completely empty!")
            return True
        else:
            print(f"[WARNING] Database still contains {total_rows} rows:")
            for table_info in non_empty_tables:
                print(f"  - {table_info}")
            return False

def main():
    """Main function"""
    cleaner = DatabaseCleaner()
    
    # Clear the database
    success = cleaner.clear_all_data()
    
    if success:
        # Verify it's empty
        cleaner.verify_empty_database()
        print("\nDatabase is ready for fresh migration!")
    else:
        print("\nDatabase clearing incomplete. Please check errors above.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)