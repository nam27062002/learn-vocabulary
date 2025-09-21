"""
Migrate all data from local SQLite (source) to the environment-configured database (target).

Safety:
- The script runs migrations on the target DB, then FLUSHes it (fully clears data) before loading.
- Requires an explicit --yes flag to proceed without interactive confirmation.

How it works:
1) Configure Django with two database aliases: 'source' (sqlite3) and 'target' (env-defined)
2) Run migrate --database target (create schema)
3) Xoá sạch dữ liệu target:
    - PostgreSQL: dùng TRUNCATE ALL TABLES ... RESTART IDENTITY CASCADE (loại trừ django_migrations)
    - Khác: fallback về django flush
4) Dump ALL data from source (bao gồm cả contenttypes, permissions, sessions, sites, social apps)
5) Load data into target
6) Reset sequences on target

Run (PowerShell):
    # Script mặc định dùng cấu hình DB server được embed sẵn bên dưới.
    # Bạn có thể override bằng cách set biến môi trường DATABASE_* nếu muốn.
    # Sau đó chạy:
  # python .\\dev_tools\\migrate_sqlite_to_env_db.py --yes

Notes:
- Media files (images) are referenced by path in DB; migrate/copy your MEDIA folder separately if moving servers.
- If you need to retain 'sites.Site' or 'socialaccount.SocialApp', remove them from the exclude list below.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.management.color import no_style  # noqa: E402
from django.db import connections  # noqa: E402
from django.apps import apps  # noqa: E402
from typing import List


def configure_databases() -> None:
    """Configure Django DATABASES with 'source' (sqlite) and 'target' (from env)."""
    base_dir = Path(__file__).resolve().parents[1]

    # Source: always the project's local sqlite
    source_db = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(base_dir / 'db.sqlite3'),
    }

    # Target: server DB (embedded defaults), overridable via environment variables
    target_db = {
        'ENGINE': os.getenv('DATABASE_ENGINE') or 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME') or 'learn_english_db_rjeh',
        'USER': os.getenv('DATABASE_USER') or 'learn_english_db_rjeh_user',
        'PASSWORD': os.getenv('DATABASE_PASSWORD') or 'rRmA7Z65LBtxIOW38q7Cpp1GxP9DZME8',
        'HOST': os.getenv('DATABASE_HOST') or 'dpg-d2v8qv15pdvs73b5p5h0-a.oregon-postgres.render.com',
        'PORT': os.getenv('DATABASE_PORT') or '5432',
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }

    sslmode = os.getenv('DATABASE_SSLMODE')
    if sslmode:
        target_db['OPTIONS'] = {'sslmode': sslmode}

    if not target_db['ENGINE'] or not target_db['NAME']:
        raise SystemExit("ERROR: DATABASE_ENGINE and DATABASE_NAME environment variables are required for target DB.")

    # Inject into Django settings
    databases = dict(settings.DATABASES) if hasattr(settings, 'DATABASES') else {}
    databases['source'] = source_db
    databases['target'] = target_db
    settings.DATABASES = databases


def test_connection(alias: str) -> None:
    """Attempt to open and close a DB connection to verify connectivity."""
    try:
        conn = connections[alias]
        conn.ensure_connection()
        conn.close()
    except Exception as e:
        raise SystemExit(f"ERROR: Failed to connect to '{alias}' database: {e}")


def _truncate_all_tables_postgres() -> None:
    """Truncate all tables on PostgreSQL target DB using CASCADE, excluding django_migrations."""
    conn = connections['target']
    engine = conn.settings_dict.get('ENGINE', '')
    if 'postgresql' not in engine:
        return
    print("[2/5] Truncating all tables on target (PostgreSQL, CASCADE)...")
    introspection = conn.introspection
    all_tables = introspection.table_names()
    # Exclude migration table to keep migration history intact
    tables = [t for t in all_tables if t != 'django_migrations']
    if not tables:
        print("No tables to truncate.")
        return
    # Quote identifiers safely
    with conn.cursor() as cursor:
        qnames = ', '.join([f'"{t}"' for t in tables])
        sql = f'TRUNCATE TABLE {qnames} RESTART IDENTITY CASCADE;'
        cursor.execute(sql)
    print("Truncate completed.")


def migrate_and_flush_target() -> None:
    """Apply migrations to target DB and then clear all data (non-interactive)."""
    print("[1/5] Applying migrations on target database...")
    call_command('migrate', database='target', interactive=False, verbosity=1)

    # Clear target data depending on backend
    conn = connections['target']
    engine = conn.settings_dict.get('ENGINE', '')
    try:
        if 'postgresql' in engine:
            _truncate_all_tables_postgres()
        else:
            print("[2/5] Flushing target database (clearing all data)...")
            call_command('flush', database='target', interactive=False, verbosity=1)
    except Exception as e:
        raise SystemExit(f"ERROR while clearing target database: {e}")


def dump_source_to_file(output_path: Path, excludes: List[str]) -> None:
    """Dump source DB to a JSON fixture file."""
    print(f"[3/5] Dumping data from source (sqlite) to {output_path} ...")
    # Write using UTF-8 to avoid Windows cp1252 encoding errors
    with open(output_path, 'w', encoding='utf-8') as f:
        call_command(
            'dumpdata',
            database='source',
            exclude=excludes,
            indent=2,
            stdout=f,
            verbosity=1,
        )


def load_fixture_to_target(fixture_path: Path) -> None:
    """Load JSON fixture into target DB."""
    print(f"[4/5] Loading data into target from {fixture_path} ...")
    call_command('loaddata', str(fixture_path), database='target', verbosity=1)


def reset_sequences_target() -> None:
    """Reset DB sequences on target to max(pk) for all models."""
    print("[5/5] Resetting sequences on target database...")
    models = apps.get_models()
    sql_list = connections['target'].ops.sequence_reset_sql(no_style(), models)
    if not sql_list:
        print("No sequence reset SQL generated (backend may not require it).")
        return
    with connections['target'].cursor() as cursor:
        for sql in sql_list:
            cursor.execute(sql)
    print("Sequence reset completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to environment-configured database")
    parser.add_argument('--yes', action='store_true', help="Run without interactive confirmation (DANGEROUS)")
    parser.add_argument('--keep-dump', action='store_true', help="Keep the generated JSON dump file")
    parser.add_argument('--dump-path', type=str, default='', help="Custom path for dump file (defaults to temp file)")
    args = parser.parse_args()

    print("Preparing Django...")
    configure_databases()
    django.setup()

    # Safety confirmation before destructive actions on target
    if not args.yes:
        print("WARNING: This will FLUSH (clear) ALL DATA from the target database and replace it with data from SQLite.")
        confirm = input("Type 'YES' to proceed: ")
        if confirm.strip().upper() != 'YES':
            print("Aborted by user.")
            sys.exit(1)

    # Test connectivity
    print("Testing DB connections...")
    test_connection('source')
    test_connection('target')

    # Migrate + Flush target
    migrate_and_flush_target()

    # Ensure DB cache table exists on target (if configured)
    try:
        from django.core.cache import caches
        default_cache = caches['default']
        cache_backend = default_cache.__class__.__module__
        if 'db' in cache_backend:
            # Create the cache table if using DatabaseCache
            location = settings.CACHES.get('default', {}).get('LOCATION', 'cache_table')
            print(f"Creating cache table '{location}' on target (if missing)...")
            call_command('createcachetable', location, database='target', verbosity=1)
    except Exception as e:
        print(f"[WARN] Skipped createcachetable: {e}")

    # Dump from source (include EVERYTHING as requested)
    excludes: List[str] = []

    if args.dump_path:
        dump_path = Path(args.dump_path).resolve()
    else:
        tmp = tempfile.NamedTemporaryFile(prefix='db_dump_', suffix='.json', delete=False)
        dump_path = Path(tmp.name)
        tmp.close()

    try:
        dump_source_to_file(dump_path, excludes)
        load_fixture_to_target(dump_path)
        reset_sequences_target()
        print("\nMigration completed successfully.")
    finally:
        if not args.keep_dump and dump_path.exists():
            try:
                dump_path.unlink()
            except Exception:
                pass


if __name__ == '__main__':
    main()
