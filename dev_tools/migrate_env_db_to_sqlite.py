"""
Migrate all data from the environment-configured database (source) to local SQLite (target).

Safety:
- By default, this script deletes the local db.sqlite3 file (wipe) before loading data.
- Requires --yes to proceed without interactive confirmation.

How it works:
1) Configure Django with two DB aliases: 'source' (env-defined server DB), 'target' (local SQLite)
2) Optionally delete local SQLite file (wipe) to ensure a clean target
3) Run migrate --database target to create schema on SQLite
4) Dump ALL data from source (bao gồm cả contenttypes, permissions, sessions, sites, social apps)
5) Load data into target
6) Reset sequences on target (no-op for SQLite)

Run (PowerShell):
  # Script mặc định dùng cấu hình DB server được embed sẵn bên dưới.
  # Bạn có thể override bằng cách set biến môi trường DATABASE_* nếu muốn.
  # Sau đó chạy:
  # python .\\dev_tools\\migrate_env_db_to_sqlite.py --yes

Notes:
- Media files (images) are not in the DB. This script only migrates database rows.
- If you want to preserve the existing local DB file, pass --no-wipe (script will still clear data via flush).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.management.color import no_style  # noqa: E402
from django.db import connections  # noqa: E402
from django.apps import apps  # noqa: E402


def configure_databases() -> Path:
    """Configure Django DATABASES with 'source' (env/server) and 'target' (local sqlite)."""
    base_dir = Path(__file__).resolve().parents[1]

    # Target (local SQLite)
    sqlite_path = base_dir / 'db.sqlite3'
    target_db = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(sqlite_path),
    }

    # Source (env/server) with embedded defaults (overridable via env)
    source_db = {
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
        source_db['OPTIONS'] = {'sslmode': sslmode}

    if not source_db['ENGINE'] or not source_db['NAME']:
        raise SystemExit("ERROR: DATABASE_ENGINE and DATABASE_NAME are required for source DB.")

    databases = dict(settings.DATABASES) if hasattr(settings, 'DATABASES') else {}
    databases['source'] = source_db
    databases['target'] = target_db
    settings.DATABASES = databases

    return sqlite_path


def test_connection(alias: str) -> None:
    try:
        conn = connections[alias]
        conn.ensure_connection()
        conn.close()
    except Exception as e:
        raise SystemExit(f"ERROR: Failed to connect to '{alias}' database: {e}")


def wipe_local_sqlite(sqlite_path: Path) -> None:
    if sqlite_path.exists():
        try:
            sqlite_path.unlink()
            print(f"Deleted local SQLite file: {sqlite_path}")
        except Exception as e:
            raise SystemExit(f"ERROR: Could not delete {sqlite_path}: {e}")


def migrate_target_sqlite() -> None:
    print("[1/5] Applying migrations on target (SQLite) database...")
    call_command('migrate', database='target', interactive=False, verbosity=1)


def flush_target_sqlite() -> None:
    print("[1/5] Flushing target (SQLite) database (clearing all data)...")
    call_command('flush', database='target', interactive=False, verbosity=1)


def dump_source_to_file(output_path: Path) -> None:
    print(f"[2/5] Dumping ALL data from source (server DB) to {output_path} ...")
    with open(output_path, 'w', encoding='utf-8') as f:
        call_command(
            'dumpdata',
            database='source',
            indent=2,
            stdout=f,
            verbosity=1,
        )


def load_fixture_to_target(fixture_path: Path) -> None:
    print(f"[3/5] Loading data into target (SQLite) from {fixture_path} ...")
    call_command('loaddata', str(fixture_path), database='target', verbosity=1)


def reset_sequences_target() -> None:
    print("[4/5] Resetting sequences on target database (if any)...")
    models = apps.get_models()
    sql_list = connections['target'].ops.sequence_reset_sql(no_style(), models)
    if not sql_list:
        print("No sequence reset SQL generated (backend may not require it).")
        return
    with connections['target'].cursor() as cursor:
        for sql in sql_list:
            cursor.execute(sql)
    print("Sequence reset completed.")


def ensure_cache_table_on_target() -> None:
    try:
        from django.core.cache import caches
        default_cache = caches['default']
        cache_backend = default_cache.__class__.__module__
        if 'db' in cache_backend:
            location = settings.CACHES.get('default', {}).get('LOCATION', 'cache_table')
            print(f"Creating cache table '{location}' on target (if missing)...")
            call_command('createcachetable', location, database='target', verbosity=1)
    except Exception as e:
        print(f"[WARN] Skipped createcachetable: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate data from server (env) DB to local SQLite")
    parser.add_argument('--yes', action='store_true', help="Run without interactive confirmation (DANGEROUS)")
    parser.add_argument('--no-wipe', action='store_true', help="Do NOT delete db.sqlite3 file; will flush instead")
    parser.add_argument('--keep-dump', action='store_true', help="Keep the generated JSON dump file")
    parser.add_argument('--dump-path', type=str, default='', help="Custom path for dump file (defaults to temp file)")
    args = parser.parse_args()

    print("Preparing Django...")
    sqlite_path = configure_databases()
    django.setup()

    if not args.yes:
        print("WARNING: This will OVERWRITE your local SQLite database with data from the server.")
        confirm = input("Type 'YES' to proceed: ")
        if confirm.strip().upper() != 'YES':
            print("Aborted by user.")
            sys.exit(1)

    print("Testing DB connections...")
    test_connection('source')

    # Prepare target (SQLite)
    if args.no_wipe:
        # Keep the file, just flush data
        migrate_target_sqlite()  # ensure schema exists
        flush_target_sqlite()
    else:
        # Delete file and recreate schema
        if sqlite_path.exists():
            wipe_local_sqlite(sqlite_path)
        migrate_target_sqlite()

    # Ensure DB cache table exists on target (if configured)
    ensure_cache_table_on_target()

    # Dump from source
    if args.dump_path:
        dump_path = Path(args.dump_path).resolve()
    else:
        tmp = tempfile.NamedTemporaryFile(prefix='db_dump_', suffix='.json', delete=False)
        dump_path = Path(tmp.name)
        tmp.close()

    try:
        dump_source_to_file(dump_path)
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
