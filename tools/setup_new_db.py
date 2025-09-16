#!/usr/bin/env python
"""
Setup New Database Script
Creates the database schema in the new database before migration
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')

def setup_database():
    """Setup the new database with Django schema"""
    print("=== Setting up New Database ===")
    
    # Temporarily update settings to point to new database
    new_db_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'learn_english_db_wuep',
        'USER': 'learn_english_db_wuep_user',
        'PASSWORD': 'RSZefSFspMPlsqz5MnxJeeUkKueWjSLH',
        'HOST': 'dpg-d32033juibrs739dn540-a.oregon-postgres.render.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
    
    # Update Django settings
    settings.DATABASES['default'] = new_db_config
    django.setup()
    
    print(f"Setting up database: {new_db_config['NAME']}")
    print(f"Host: {new_db_config['HOST']}")
    print()
    
    try:
        # Run migrations
        print("Running Django migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
        print("\n[OK] Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to setup database: {e}")
        return False

if __name__ == '__main__':
    success = setup_database()
    if success:
        print("\nYou can now run the migration tool:")
        print("python tools/migrate_database.py")
    sys.exit(0 if success else 1)