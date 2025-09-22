"""
Migrate all data from the current environment-configured DB (source) to a NEW server DB (target).

Safety:
- Target DB will be cleared completely (TRUNCATE ... CASCADE for PostgreSQL) before loading data.
- Requires --yes to proceed without interactive confirmation.

How it works:
1) Configure two database aliases: 'source' (current env/server DB) and 'target' (new server DB)
2) (Optional) Rebuild target schema for PostgreSQL when --rebuild-schema is set:
    - DROP SCHEMA public CASCADE; CREATE SCHEMA public; (removes migrations history too)
    - Then run migrate --database target to create schema fresh
    Otherwise: run migrate --database target to create/update schema
3) Clear target DB:
   - PostgreSQL: TRUNCATE ALL TABLES ... RESTART IDENTITY CASCADE (exclude django_migrations)
   - Others: fallback to django flush
4) Dump ALL data from source (UTF-8) including system tables
5) Load data into target
6) Reset sequences on target

Run (PowerShell):
  # Default source is taken from current env (.env). Target can be passed via args or uses embedded defaults below.
    # Example using embedded defaults (keeps schema):
    # python .\\dev_tools\\migrate_env_db_to_new_server.py --yes
    # Nếu target từng được dùng với schema cũ (thiếu cột), nên rebuild schema:
    # python .\\dev_tools\\migrate_env_db_to_new_server.py --yes --rebuild-schema

  # Or override target via CLI args:
  # python .\\dev_tools\\migrate_env_db_to_new_server.py --yes `
  #   --target-name learn_english_db_wuep `
  #   --target-user learn_english_db_wuep_user `
  #   --target-password RSZefSFspMPlsqz5MnxJeeUkKueWjSLH `
  #   --target-host dpg-d32033juibrs739dn540-a.oregon-postgres.render.com `
  #   --target-port 5432

Notes:
- Media files are not moved by this script.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import List

# Ensure project root is on sys.path so 'learn_english_project' is importable
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learn_english_project.settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.management.color import no_style  # noqa: E402
from django.db import connections  # noqa: E402
from django.apps import apps  # noqa: E402


def configure_databases(args) -> None:
    """Configure Django DATABASES with 'source' (current env) and 'target' (new server)."""
    # Source from env (existing server)
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

    # Target from args with embedded defaults
    target_db = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': args.target_name or 'learn_english_db_wuep',
        'USER': args.target_user or 'learn_english_db_wuep_user',
        'PASSWORD': args.target_password or 'RSZefSFspMPlsqz5MnxJeeUkKueWjSLH',
        'HOST': args.target_host or 'dpg-d32033juibrs739dn540-a.oregon-postgres.render.com',
        'PORT': str(args.target_port or '5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }

    sslmode = os.getenv('DATABASE_SSLMODE')
    if sslmode:
        source_db['OPTIONS'] = {'sslmode': sslmode}
        target_db.setdefault('OPTIONS', {})['sslmode'] = sslmode

    databases = dict(settings.DATABASES) if hasattr(settings, 'DATABASES') else {}
    databases['source'] = source_db
    databases['target'] = target_db
    settings.DATABASES = databases


def test_connection(alias: str) -> None:
    try:
        conn = connections[alias]
        conn.ensure_connection()
        conn.close()
    except Exception as e:
        raise SystemExit(f"ERROR: Failed to connect to '{alias}' database: {e}")


def rebuild_postgres_schema_target() -> None:
    """Drop and recreate 'public' schema on target PostgreSQL DB, then run migrate.

    This resets the entire schema (including django_migrations), ensuring a clean state
    for running migrations and matching the current models.
    """
    conn = connections['target']
    engine = conn.settings_dict.get('ENGINE', '')
    if 'postgresql' not in engine:
        print("[1/6] Target is not PostgreSQL; skipping schema rebuild.")
        return
    print("[1/6] Dropping and recreating 'public' schema on target (PostgreSQL)...")
    with conn.cursor() as cursor:
        cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
    print("Schema recreated. Running migrations fresh on target...")
    call_command('migrate', database='target', interactive=False, verbosity=1)


def truncate_all_tables_postgres(alias: str, step_prefix: str) -> None:
    conn = connections[alias]
    engine = conn.settings_dict.get('ENGINE', '')
    if 'postgresql' not in engine:
        print(f"{step_prefix} Flushing target database (non-PostgreSQL)...")
        call_command('flush', database=alias, interactive=False, verbosity=1)
        return
    print(f"{step_prefix} Truncating all tables on {alias} (PostgreSQL, CASCADE)...")
    introspection = conn.introspection
    all_tables = introspection.table_names()
    tables = [t for t in all_tables if t != 'django_migrations']
    if not tables:
        print("No tables to truncate.")
        return
    with conn.cursor() as cursor:
        qnames = ', '.join([f'"{t}"' for t in tables])
        sql = f'TRUNCATE TABLE {qnames} RESTART IDENTITY CASCADE;'
        cursor.execute(sql)
    print("Truncate completed.")


def migrate_target_schema() -> None:
    print("[1/6] Applying migrations on target (new server) database...")
    call_command('migrate', database='target', interactive=False, verbosity=1)


def dump_source_all(output_path: Path) -> None:
    print(f"[2/6] Dumping ALL data from source (current server) to {output_path} ...")
    with open(output_path, 'w', encoding='utf-8') as f:
        call_command('dumpdata', database='source', indent=2, stdout=f, verbosity=1)


def load_into_target(fixture_path: Path) -> None:
    print(f"[5/6] Loading data into target (new server) from {fixture_path} ...")
    call_command('loaddata', str(fixture_path), database='target', verbosity=1)


def reset_sequences_target() -> None:
    print("[6/6] Resetting sequences on target database...")
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
    parser = argparse.ArgumentParser(description="Migrate data from current env DB to NEW server DB")
    parser.add_argument('--yes', action='store_true', help="Run without interactive confirmation (DANGEROUS)")
    parser.add_argument('--keep-dump', action='store_true', help="Keep the generated JSON dump file")
    parser.add_argument('--dump-path', type=str, default='', help="Custom path for dump file (defaults to temp file)")
    parser.add_argument('--rebuild-schema', action='store_true', help="Drop and recreate target PostgreSQL schema before migrating")
    # Optional target overrides
    parser.add_argument('--target-name', type=str)
    parser.add_argument('--target-user', type=str)
    parser.add_argument('--target-password', type=str)
    parser.add_argument('--target-host', type=str)
    parser.add_argument('--target-port', type=str)
    args = parser.parse_args()

    print("Preparing Django...")
    configure_databases(args)
    django.setup()

    if not args.yes:
        print("WARNING: This will FLUSH (clear) ALL DATA from the target server DB and replace it with data from the current server.")
        confirm = input("Type 'YES' to proceed: ")
        if confirm.strip().upper() != 'YES':
            print("Aborted by user.")
            sys.exit(1)

    print("Testing DB connections...")
    test_connection('source')
    test_connection('target')

    # 1) Prepare/Migrate target schema
    if args.rebuild_schema:
        rebuild_postgres_schema_target()
    else:
        migrate_target_schema()

    # 2) Clear target data
    truncate_all_tables_postgres(alias='target', step_prefix='[3/6]')

    # 3) Dump from source
    if args.dump_path:
        dump_path = Path(args.dump_path).resolve()
    else:
        tmp = tempfile.NamedTemporaryFile(prefix='db_dump_', suffix='.json', delete=False)
        dump_path = Path(tmp.name)
        tmp.close()

    try:
        dump_source_all(dump_path)
        # 4) Load into target
        load_into_target(dump_path)
        # 5) Reset sequences
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
