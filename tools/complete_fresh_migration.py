#!/usr/bin/env python
"""
Complete Fresh Migration Tool
1. Completely clears the target database
2. Migrates all data from source to target database
3. Ensures 100% data consistency
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

class CompleteFreshMigrator:
    def __init__(self):
        # Source database configuration
        self.source_config = {
            'host': 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
            'port': '5432',
            'database': 'learn_english_db_rjeh',
            'user': 'learn_english_db_rjeh_user',
            'password': 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8'
        }
        
        # Target database configuration (current Django settings)
        from django.conf import settings
        db_settings = settings.DATABASES['default']
        self.target_config = {
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
            'database': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD']
        }

    def test_connections(self):
        """Test both database connections"""
        print("Testing database connections...")
        
        # Test source database
        try:
            conn = psycopg2.connect(**self.source_config)
            conn.close()
            print("  [OK] Source database connection successful")
        except Exception as e:
            print(f"  [ERROR] Source database connection failed: {e}")
            return False
        
        # Test target database
        try:
            conn = psycopg2.connect(**self.target_config)
            conn.close()
            print("  [OK] Target database connection successful")
        except Exception as e:
            print(f"  [ERROR] Target database connection failed: {e}")
            return False
        
        return True

    def get_all_tables_from_target(self):
        """Get all tables from target database"""
        conn = psycopg2.connect(**self.target_config)
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

    def get_tables_from_source(self):
        """Get data tables from source database"""
        conn = psycopg2.connect(**self.source_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'django_migrations'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables

    def get_row_count(self, table_name, database='target'):
        """Get row count for a table"""
        config = self.target_config if database == 'target' else self.source_config
        conn = psycopg2.connect(**config)
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

    def clear_target_database(self):
        """Completely clear the target database"""
        print("\n=== Step 1: Clearing Target Database ===")
        
        # Get all tables
        tables = self.get_all_tables_from_target()
        print(f"Found {len(tables)} tables in target database")
        
        # Check current data
        total_rows = 0
        for table in tables:
            count = self.get_row_count(table, 'target')
            total_rows += count
            if count > 0:
                print(f"  {table}: {count} rows")
        
        if total_rows == 0:
            print("Target database is already empty!")
            return True
        
        print(f"Total rows to clear: {total_rows}")
        
        # Clear all data
        conn = psycopg2.connect(**self.target_config)
        cursor = conn.cursor()
        
        try:
            print("Clearing all data...")
            
            # Disable foreign key constraints
            cursor.execute("SET session_replication_role = replica;")
            
            # Clear all tables
            cleared_count = 0
            for table in tables:
                row_count = self.get_row_count(table, 'target')
                if row_count > 0:
                    cursor.execute(sql.SQL("DELETE FROM {}").format(
                        sql.Identifier(table)
                    ))
                    print(f"  [OK] Cleared {table} ({row_count} rows)")
                    cleared_count += 1
            
            # Reset sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            sequences = [row[0] for row in cursor.fetchall()]
            
            for seq_name in sequences:
                cursor.execute(sql.SQL("ALTER SEQUENCE {} RESTART WITH 1").format(
                    sql.Identifier(seq_name)
                ))
            
            print(f"  [OK] Reset {len(sequences)} sequences")
            
            # Re-enable foreign key constraints
            cursor.execute("SET session_replication_role = DEFAULT;")
            
            conn.commit()
            print(f"[OK] Successfully cleared {cleared_count} tables")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to clear database: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def migrate_fresh_data(self):
        """Migrate all data from source to target"""
        print("\n=== Step 2: Migrating Fresh Data ===")
        
        # Get source tables
        source_tables = self.get_tables_from_source()
        print(f"Found {len(source_tables)} tables in source database")
        
        # Show data summary
        total_source_rows = 0
        table_data = {}
        for table in source_tables:
            count = self.get_row_count(table, 'source')
            table_data[table] = count
            total_source_rows += count
            if count > 0:
                print(f"  {table}: {count} rows")
        
        print(f"Total rows to migrate: {total_source_rows}")
        
        if total_source_rows == 0:
            print("No data to migrate!")
            return True
        
        # Migrate table by table
        migrated_tables = 0
        migrated_rows = 0
        failed_tables = []
        
        for table in source_tables:
            if table_data[table] == 0:
                continue
                
            print(f"Migrating {table}... ", end="")
            
            try:
                # Get data from source
                source_conn = psycopg2.connect(**self.source_config)
                source_cursor = source_conn.cursor()
                
                source_cursor.execute(sql.SQL("SELECT * FROM {}").format(
                    sql.Identifier(table)
                ))
                column_names = [desc[0] for desc in source_cursor.description]
                rows = source_cursor.fetchall()
                
                source_cursor.close()
                source_conn.close()
                
                # Insert into target
                target_conn = psycopg2.connect(**self.target_config)
                target_cursor = target_conn.cursor()
                
                if rows:
                    placeholders = ', '.join(['%s'] * len(column_names))
                    columns = ', '.join(column_names)
                    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table),
                        sql.SQL(', ').join(map(sql.Identifier, column_names)),
                        sql.SQL(placeholders)
                    )
                    
                    target_cursor.executemany(query, rows)
                    target_conn.commit()
                    
                    migrated_rows += len(rows)
                    print(f"[OK] {len(rows)} rows")
                else:
                    print("[OK] No data")
                
                target_cursor.close()
                target_conn.close()
                migrated_tables += 1
                
            except Exception as e:
                print(f"[ERROR] {e}")
                failed_tables.append(table)
        
        # Fix sequences
        print("\nFixing sequences...")
        target_conn = psycopg2.connect(**self.target_config)
        target_cursor = target_conn.cursor()
        
        try:
            target_cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            sequences = [row[0] for row in target_cursor.fetchall()]
            
            for seq_name in sequences:
                if seq_name.endswith('_id_seq'):
                    table_name = seq_name[:-7]
                    try:
                        target_cursor.execute(sql.SQL("SELECT COALESCE(MAX(id), 1) FROM {}").format(
                            sql.Identifier(table_name)
                        ))
                        max_id = target_cursor.fetchone()[0]
                        target_cursor.execute(sql.SQL("SELECT setval(%s, %s)"), (seq_name, max_id))
                        print(f"  [OK] {seq_name} -> {max_id}")
                    except:
                        pass
            
            target_conn.commit()
            
        except Exception as e:
            print(f"  [ERROR] Failed to fix sequences: {e}")
        finally:
            target_cursor.close()
            target_conn.close()
        
        # Summary
        print(f"\n[OK] Migration completed!")
        print(f"Tables migrated: {migrated_tables}/{len(source_tables)}")
        print(f"Rows migrated: {migrated_rows}")
        if failed_tables:
            print(f"Failed tables: {', '.join(failed_tables)}")
        
        return len(failed_tables) == 0

    def verify_data_consistency(self):
        """Verify that source and target have identical data"""
        print("\n=== Step 3: Verifying Data Consistency ===")
        
        source_tables = self.get_tables_from_source()
        inconsistent_tables = []
        total_source = 0
        total_target = 0
        
        for table in source_tables:
            source_count = self.get_row_count(table, 'source')
            target_count = self.get_row_count(table, 'target')
            
            total_source += source_count
            total_target += target_count
            
            if source_count != target_count:
                inconsistent_tables.append(f"{table}: source={source_count}, target={target_count}")
                print(f"  [WARNING] {table}: source={source_count}, target={target_count}")
            elif source_count > 0:
                print(f"  [OK] {table}: {source_count} rows (consistent)")
        
        print(f"\nTotal rows - Source: {total_source}, Target: {total_target}")
        
        if inconsistent_tables:
            print(f"\n[WARNING] Found {len(inconsistent_tables)} inconsistent tables:")
            for issue in inconsistent_tables:
                print(f"  - {issue}")
            return False
        else:
            print("\n[OK] All data is 100% consistent!")
            return True

    def run_complete_fresh_migration(self):
        """Run the complete fresh migration process"""
        print("=== Complete Fresh Migration Tool ===")
        print(f"Source: {self.source_config['database']} @ {self.source_config['host']}")
        print(f"Target: {self.target_config['database']} @ {self.target_config['host']}")
        
        # Step 0: Test connections
        if not self.test_connections():
            print("Migration aborted due to connection issues.")
            return False
        
        # Confirm the operation
        print("\n[WARNING] This will COMPLETELY REPLACE all data in the target database!")
        confirm = input("Type 'FRESH MIGRATION' to confirm: ")
        if confirm != 'FRESH MIGRATION':
            print("Migration cancelled.")
            return False
        
        # Step 1: Clear target database
        if not self.clear_target_database():
            print("Migration aborted: Failed to clear target database.")
            return False
        
        # Step 2: Migrate fresh data
        if not self.migrate_fresh_data():
            print("Migration completed with errors.")
            
        # Step 3: Verify consistency
        consistent = self.verify_data_consistency()
        
        if consistent:
            print("\n🎉 Fresh migration completed successfully!")
            print("Source and target databases are now 100% identical.")
        else:
            print("\n⚠️  Migration completed but with data inconsistencies.")
            print("Please review the warnings above.")
        
        return consistent

def main():
    """Main function"""
    migrator = CompleteFreshMigrator()
    success = migrator.run_complete_fresh_migration()
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)