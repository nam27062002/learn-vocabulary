"""
Database configuration for sync tool
"""
import os
from pathlib import Path

# Server PostgreSQL Configuration
SERVER_DB_CONFIG = {
    'ENGINE': 'postgresql',
    'NAME': 'learn_english_db_rjeh',
    'USER': 'learn_english_db_rjeh_user',
    'PASSWORD': 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8',
    'HOST': 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
    'PORT': '5432',
}

# Local SQLite Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DB_CONFIG = {
    'ENGINE': 'sqlite3',
    'NAME': str(BASE_DIR / 'db.sqlite3'),
}

# Database connection strings
SERVER_CONNECTION_STRING = (
    f"postgresql://{SERVER_DB_CONFIG['USER']}:"
    f"{SERVER_DB_CONFIG['PASSWORD']}@"
    f"{SERVER_DB_CONFIG['HOST']}:"
    f"{SERVER_DB_CONFIG['PORT']}/"
    f"{SERVER_DB_CONFIG['NAME']}"
)

LOCAL_CONNECTION_STRING = f"sqlite:///{LOCAL_DB_CONFIG['NAME']}"

# Tables to sync (Django app tables)
TABLES_TO_SYNC = [
    'auth_user',
    'auth_group',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'auth_permission',
    'django_content_type',
    'django_admin_log',
    'django_session',
    'django_migrations',
    'accounts_user',
    'vocabulary_deck',
    'vocabulary_flashcard',
    'vocabulary_definition',
    'vocabulary_studysession',
    'vocabulary_studysessionanswer',
    'vocabulary_dailystatistics',
    'vocabulary_weeklystatistics',
    'vocabulary_incorrectwordreview',
    'vocabulary_favoriteflashcard',
    'vocabulary_blacklistflashcard',
]