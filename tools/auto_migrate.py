#!/usr/bin/env python
"""
Automatic Database Migration Tool
Migrates all data from old to new database without prompts
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

class AutoMigrator:
    def __init__(self):
        # Old database configuration
        self.old_db_config = {
            'host': 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
            'port': '5432',
            'database': 'learn_english_db_rjeh',
            'user': 'learn_english_db_rjeh_user',
            'password': 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8'
        }
        
        # New database configuration (current Django settings)
        from django.conf import settings
        db_settings = settings.DATABASES['default']
        self.new_db_config = {
            'host': db_settings['HOST'],
            'port': db_settings['PORT'],
            'database': db_settings['NAME'],
            'user': db_settings['USER'],
            'password': db_settings['PASSWORD']
        }

    def get_table_list(self):
        """Get list of all data tables from old database"""
        conn = psycopg2.connect(**self.old_db_config)
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

    def migrate_table(self, table_name):
        """Migrate data from one table"""
        print(f"Migrating {table_name}...")
        
        # Get data from old database
        old_conn = psycopg2.connect(**self.old_db_config)
        old_cursor = old_conn.cursor()
        
        try:
            old_cursor.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
            column_names = [desc[0] for desc in old_cursor.description]
            rows = old_cursor.fetchall()
        except Exception as e:
            print(f"  [SKIP] Could not read from {table_name}: {e}")
            old_cursor.close()
            old_conn.close()
            return True
        
        old_cursor.close()
        old_conn.close()
        
        if not rows:
            print(f"  [OK] No data in {table_name}")
            return True
        
        # Insert data into new database
        new_conn = psycopg2.connect(**self.new_db_config)
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
            return True
            
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")
            new_conn.rollback()
            return False
        finally:
            new_cursor.close()
            new_conn.close()

    def fix_sequences(self):
        """Fix PostgreSQL sequences"""
        print("Fixing sequences...")
        
        conn = psycopg2.connect(**self.new_db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            
            sequences = [row[0] for row in cursor.fetchall()]
            
            for seq_name in sequences:
                if seq_name.endswith('_id_seq'):
                    table_name = seq_name[:-7]
                    
                    try:
                        cursor.execute(sql.SQL("SELECT COALESCE(MAX(id), 1) FROM {}").format(
                            sql.Identifier(table_name)
                        ))
                        max_id = cursor.fetchone()[0]
                        cursor.execute(sql.SQL("SELECT setval(%s, %s)"), (seq_name, max_id))
                        print(f"  [OK] {seq_name} -> {max_id}")
                    except:
                        pass
            
            conn.commit()
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def run(self):
        print("=== Auto Database Migration ===")
        
        tables = self.get_table_list()
        print(f"Found {len(tables)} tables to migrate")
        
        failed = 0
        for table in tables:
            if not self.migrate_table(table):
                failed += 1
        
        self.fix_sequences()
        
        print(f"\n=== Complete ===")
        print(f"Total: {len(tables)}, Success: {len(tables)-failed}, Failed: {failed}")
        
        return failed == 0

if __name__ == '__main__':
    migrator = AutoMigrator()
    success = migrator.run()
    sys.exit(0 if success else 1)