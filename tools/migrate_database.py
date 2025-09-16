#!/usr/bin/env python
"""
Database Migration Tool
Migrates all data from old PostgreSQL database to new PostgreSQL database
"""

import os
import sys
import django
import psycopg2
from psycopg2 import sql
from django.db import connections
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

class DatabaseMigrator:
    def __init__(self):
        # Old database configuration
        self.old_db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'learn_english_db_rjeh',
            'USER': 'learn_english_db_rjeh_user',
            'PASSWORD': 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8',
            'HOST': 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
            'PORT': '5432',
        }
        
        # New database configuration
        self.new_db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'learn_english_db_wuep',
            'USER': 'learn_english_db_wuep_user',
            'PASSWORD': 'RSZefSFspMPlsqz5MnxJeeUkKueWjSLH',
            'HOST': 'dpg-d32033juibrs739dn540-a.oregon-postgres.render.com',
            'PORT': '5432',
        }
        
        # Configure Django database connections
        settings.DATABASES['old_db'] = self.old_db_config
        settings.DATABASES['new_db'] = self.new_db_config

    def test_connections(self):
        """Test connections to both databases"""
        print("Testing database connections...")
        
        try:
            # Test old database
            old_conn = psycopg2.connect(
                host=self.old_db_config['HOST'],
                port=self.old_db_config['PORT'],
                database=self.old_db_config['NAME'],
                user=self.old_db_config['USER'],
                password=self.old_db_config['PASSWORD']
            )
            old_conn.close()
            print("[OK] Old database connection successful")
        except Exception as e:
            print(f"[ERROR] Old database connection failed: {e}")
            return False
            
        try:
            # Test new database
            new_conn = psycopg2.connect(
                host=self.new_db_config['HOST'],
                port=self.new_db_config['PORT'],
                database=self.new_db_config['NAME'],
                user=self.new_db_config['USER'],
                password=self.new_db_config['PASSWORD']
            )
            new_conn.close()
            print("[OK] New database connection successful")
        except Exception as e:
            print(f"[ERROR] New database connection failed: {e}")
            return False
            
        return True

    def get_table_list(self):
        """Get list of all tables from old database"""
        conn = psycopg2.connect(
            host=self.old_db_config['HOST'],
            port=self.old_db_config['PORT'],
            database=self.old_db_config['NAME'],
            user=self.old_db_config['USER'],
            password=self.old_db_config['PASSWORD']
        )
        
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

    def get_table_data_count(self, table_name):
        """Get row count for a table in old database"""
        conn = psycopg2.connect(
            host=self.old_db_config['HOST'],
            port=self.old_db_config['PORT'],
            database=self.old_db_config['NAME'],
            user=self.old_db_config['USER'],
            password=self.old_db_config['PASSWORD']
        )
        
        cursor = conn.cursor()
        cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        ))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return count

    def migrate_table(self, table_name):
        """Migrate data from one table"""
        print(f"Migrating table: {table_name}")
        
        # Get data from old database
        old_conn = psycopg2.connect(
            host=self.old_db_config['HOST'],
            port=self.old_db_config['PORT'],
            database=self.old_db_config['NAME'],
            user=self.old_db_config['USER'],
            password=self.old_db_config['PASSWORD']
        )
        
        old_cursor = old_conn.cursor()
        old_cursor.execute(sql.SQL("SELECT * FROM {}").format(
            sql.Identifier(table_name)
        ))
        
        # Get column names
        column_names = [desc[0] for desc in old_cursor.description]
        rows = old_cursor.fetchall()
        
        old_cursor.close()
        old_conn.close()
        
        if not rows:
            print(f"  No data to migrate for {table_name}")
            return True
        
        # Insert data into new database
        new_conn = psycopg2.connect(
            host=self.new_db_config['HOST'],
            port=self.new_db_config['PORT'],
            database=self.new_db_config['NAME'],
            user=self.new_db_config['USER'],
            password=self.new_db_config['PASSWORD']
        )
        
        new_cursor = new_conn.cursor()
        
        try:
            # Clear existing data
            new_cursor.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                sql.Identifier(table_name)
            ))
            
            # Prepare insert statement
            placeholders = ', '.join(['%s'] * len(column_names))
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, column_names)),
                sql.SQL(placeholders)
            )
            
            # Insert all rows
            new_cursor.executemany(insert_query, rows)
            new_conn.commit()
            
            print(f"  [OK] Migrated {len(rows)} rows")
            
        except Exception as e:
            print(f"  [ERROR] Failed to migrate {table_name}: {e}")
            new_conn.rollback()
            return False
        finally:
            new_cursor.close()
            new_conn.close()
            
        return True

    def fix_sequences(self):
        """Fix PostgreSQL sequences after data migration"""
        print("Fixing PostgreSQL sequences...")
        
        conn = psycopg2.connect(
            host=self.new_db_config['HOST'],
            port=self.new_db_config['PORT'],
            database=self.new_db_config['NAME'],
            user=self.new_db_config['USER'],
            password=self.new_db_config['PASSWORD']
        )
        
        cursor = conn.cursor()
        
        try:
            # Get all sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            
            sequences = [row[0] for row in cursor.fetchall()]
            
            for seq_name in sequences:
                # Extract table and column name from sequence
                if seq_name.endswith('_id_seq'):
                    table_name = seq_name[:-7]  # Remove '_id_seq'
                    
                    # Get max ID from table
                    cursor.execute(sql.SQL("SELECT COALESCE(MAX(id), 1) FROM {}").format(
                        sql.Identifier(table_name)
                    ))
                    max_id = cursor.fetchone()[0]
                    
                    # Update sequence
                    cursor.execute(sql.SQL("SELECT setval(%s, %s)"), (seq_name, max_id))
                    print(f"  [OK] Fixed sequence {seq_name} (set to {max_id})")
            
            conn.commit()
            
        except Exception as e:
            print(f"  [ERROR] Failed to fix sequences: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def setup_new_database(self):
        """Setup the new database with proper schema using Django migrations"""
        print("\nSetting up new database schema...")
        
        # Temporarily update Django settings to use the new database
        original_db_config = settings.DATABASES['default'].copy()
        settings.DATABASES['default'] = self.new_db_config
        
        try:
            # Run Django migrations to create all tables
            from django.core.management import execute_from_command_line
            import sys
            
            # Save original argv
            original_argv = sys.argv.copy()
            
            # Run migrate command
            sys.argv = ['manage.py', 'migrate', '--verbosity=1']
            execute_from_command_line(sys.argv)
            
            # Restore original argv
            sys.argv = original_argv
            
            print("[OK] Database schema created successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to setup database schema: {e}")
            return False
        finally:
            # Restore original database configuration
            settings.DATABASES['default'] = original_db_config

    def run_migration(self):
        """Run the complete migration process"""
        print("=== Database Migration Tool ===")
        print(f"From: {self.old_db_config['NAME']} @ {self.old_db_config['HOST']}")
        print(f"To: {self.new_db_config['NAME']} @ {self.new_db_config['HOST']}")
        print()
        
        # Test connections
        if not self.test_connections():
            print("Migration aborted due to connection issues.")
            return False
        
        # Setup new database schema
        if not self.setup_new_database():
            print("Migration aborted due to schema setup issues.")
            return False
        
        # Get confirmation
        print("\n[WARNING] This will OVERWRITE all data in the new database!")
        confirm = input("Are you sure you want to continue? (type 'YES' to confirm): ")
        if confirm != 'YES':
            print("Migration cancelled.")
            return False
        
        # Get table list
        print("\nGetting table list...")
        tables = self.get_table_list()
        print(f"Found {len(tables)} tables to migrate")
        
        # Show data summary
        print("\nData summary:")
        total_rows = 0
        for table in tables:
            count = self.get_table_data_count(table)
            total_rows += count
            print(f"  {table}: {count} rows")
        
        print(f"\nTotal rows to migrate: {total_rows}")
        
        # Start migration
        print("\n=== Starting Migration ===")
        failed_tables = []
        
        for table in tables:
            if not self.migrate_table(table):
                failed_tables.append(table)
        
        # Fix sequences
        self.fix_sequences()
        
        # Summary
        print("\n=== Migration Complete ===")
        if failed_tables:
            print(f"[ERROR] Failed to migrate {len(failed_tables)} tables:")
            for table in failed_tables:
                print(f"  - {table}")
        else:
            print("[OK] All tables migrated successfully!")
        
        print(f"Total tables processed: {len(tables)}")
        print(f"Successful: {len(tables) - len(failed_tables)}")
        print(f"Failed: {len(failed_tables)}")
        
        return len(failed_tables) == 0

if __name__ == '__main__':
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    sys.exit(0 if success else 1)