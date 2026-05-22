"""
Database migration runner.

Automatically executes SQL migration files from the migrations/ folder
and tracks them in the migrations table.

Usage:
    python -m script.run_migrations
    python -m script.run_migrations --reset  # Clear migration records and re-run
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict
from urllib.parse import quote, urlparse
from src.infrastructure.clients.supabase import get_supabase_service
import psycopg2
from dotenv import dotenv_values, load_dotenv

load_dotenv()

BACK_DIR = Path(__file__).resolve().parents[1]


def get_migration_files() -> List[Dict[str, str]]:
    """Get all migration files sorted by name."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        print(f"Migrations directory not found: {migrations_dir}")
        return []
    
    migration_files = []
    for file_path in sorted(migrations_dir.glob("*.sql")):
        with open(file_path, 'r') as f:
            content = f.read()
            checksum = hashlib.sha256(content.encode()).hexdigest()
        
        migration_files.append({
            "name": file_path.name,
            "path": str(file_path),
            "content": content,
            "checksum": checksum
        })
    
    return migration_files


def get_executed_migrations(supabase) -> set:
    """Get list of migrations that have already been executed."""
    try:
        response = supabase.table("migrations").select("migration_name").execute()
        return {row["migration_name"] for row in response.data} if response.data else set()
    except Exception as e:
        print(f"Error fetching executed migrations: {e}")
        print("Note: If migrations table doesn't exist, run schema/migrations.sql first")
        return set()


def get_shared_supabase_env() -> dict[str, str]:
    """Load the shared Supabase env file referenced by SUPABASE_ENV_FILE."""
    shared_env_rel = os.getenv("SUPABASE_ENV_FILE", "../supabase/.env.prod")
    shared_env_path = Path(shared_env_rel)
    if not shared_env_path.is_absolute():
        shared_env_path = (BACK_DIR / shared_env_path).resolve()

    if not shared_env_path.exists():
        return {}

    return {
        str(key): str(value)
        for key, value in dotenv_values(shared_env_path).items()
        if key and value is not None
    }


def build_admin_db_url_from_shared_env() -> tuple[str, str] | None:
    """Derive a migration URL from the shared Supabase env file when possible."""
    shared_env = get_shared_supabase_env()
    postgres_password = shared_env.get("POSTGRES_PASSWORD")
    if not postgres_password:
        return None

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        scheme = parsed.scheme or "postgresql"
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        database = (parsed.path or "").lstrip("/") or "postgres"
        username = parsed.username or ""
        tenant_suffix = username.split(".", 1)[1] if "." in username else ""
        admin_username = f"supabase_admin.{tenant_suffix}" if tenant_suffix else "supabase_admin"
        admin_url = (
            f"{scheme}://{admin_username}:{quote(postgres_password, safe='')}"
            f"@{host}:{port}/{database}"
        )
        return "SUPABASE_ENV_FILE", admin_url

    host = shared_env.get("POSTGRES_HOST", "localhost")
    port = shared_env.get("POSTGRES_PORT", "5432")
    database = shared_env.get("POSTGRES_DB", "postgres")
    admin_url = (
        f"postgresql://supabase_admin:{quote(postgres_password, safe='')}"
        f"@{host}:{port}/{database}"
    )
    return "SUPABASE_ENV_FILE", admin_url


def get_migration_db_url() -> tuple[str, str]:
    """Resolve the PostgreSQL URL used for schema migrations."""
    candidates = [
        "MIGRATION_DATABASE_URL",
        "ADMIN_DATABASE_URL",
    ]

    for env_name in candidates:
        db_url = os.getenv(env_name)
        if db_url:
            return env_name, db_url

    derived_admin_url = build_admin_db_url_from_shared_env()
    if derived_admin_url:
        return derived_admin_url

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return "DATABASE_URL", database_url

    raise ValueError(
        "No PostgreSQL URL configured for migrations. "
        "Set MIGRATION_DATABASE_URL, ADMIN_DATABASE_URL, DATABASE_URL, "
        "or SUPABASE_ENV_FILE with POSTGRES_PASSWORD."
    )


def mask_db_url(db_url: str) -> str:
    """Return a log-safe representation of a PostgreSQL URL."""
    parsed = urlparse(db_url)
    if not parsed.scheme:
        return "<invalid database url>"

    auth = parsed.username or "<unknown-user>"
    if parsed.password:
        auth = f"{auth}:***"

    host = parsed.hostname or "<unknown-host>"
    port = parsed.port or 5432
    database = (parsed.path or "").lstrip("/") or "postgres"
    return f"{parsed.scheme}://{auth}@{host}:{port}/{database}"


def get_db_connection():
    """Get direct PostgreSQL connection with admin privileges."""
    env_name, db_url = get_migration_db_url()

    print(f"ℹ Connecting to database with {env_name}: {mask_db_url(db_url)}")
    conn = psycopg2.connect(db_url)

    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT current_user, has_schema_privilege(current_user, 'public', 'CREATE')
            """
        )
        current_user, can_create_public = cursor.fetchone()

    if not can_create_public:
        conn.close()
        raise PermissionError(
            "Connected as role "
            f"'{current_user}', but it does not have CREATE privilege on schema 'public'. "
            "Use MIGRATION_DATABASE_URL (or ADMIN_DATABASE_URL) with a schema-owning/admin role, "
            "or grant CREATE on schema public to the configured role."
        )

    return conn


def execute_migration(supabase, migration: Dict[str, str], auto_confirm: bool = False) -> bool:
    """Execute a single migration and record it."""
    print(f"\n▶ Executing migration: {migration['name']}")
    print(f"  Checksum: {migration['checksum'][:16]}...")
    
    print(f"\n{'='*60}")
    print(f"Migration SQL ({migration['name']}):")
    print(f"{'='*60}")
    print(migration['content'])
    print(f"{'='*60}\n")
    
    if not auto_confirm:
        confirm = input(f"Execute this migration? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print(f"⏭  Skipping migration: {migration['name']}")
            return False
    
    try:
        # Execute SQL directly using psycopg2
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(migration['content'])
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Record the migration as executed
        supabase.table("migrations").insert({
            "migration_name": migration['name'],
            "checksum": migration['checksum']
        }).execute()
        
        print(f"✓ Migration executed and recorded: {migration['name']}")
        return True
        
    except Exception as e:
        print(f"✗ Error executing migration {migration['name']}: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_migration(supabase, migration_name: str):
    """Remove a migration record to allow re-execution."""
    try:
        supabase.table("migrations").delete().eq("migration_name", migration_name).execute()
        print(f"✓ Removed migration record: {migration_name}")
    except Exception as e:
        print(f"✗ Error removing migration record: {e}")


def run_migrations(reset: bool = False):
    """Run all pending migrations."""
    print("Starting migration process...")
    
    supabase = get_supabase_service()
    
    # Get all migration files
    migration_files = get_migration_files()
    if not migration_files:
        print("No migration files found.")
        return
    
    print(f"Found {len(migration_files)} migration file(s)")
    
    # Get already executed migrations
    executed = get_executed_migrations(supabase)
    print(f"Already executed: {len(executed)} migration(s)")
    
    # Reset if requested
    if reset and executed:
        print("\n⚠ RESET MODE: Clearing migration records...")
        for migration_name in executed:
            reset_migration(supabase, migration_name)
        executed = set()
    
    # Find pending migrations
    pending = [m for m in migration_files if m['name'] not in executed]
    
    if not pending:
        print("\n✓ All migrations are up to date!")
        return
    
    print(f"\nPending migrations: {len(pending)}")
    for migration in pending:
        print(f"  - {migration['name']}")
    
    # Execute pending migrations
    executed_count = 0
    for migration in pending:
        if execute_migration(supabase, migration):
            executed_count += 1
        else:
            print(f"\n⚠ Migration halted at: {migration['name']}")
            break
    
    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  Executed: {executed_count}/{len(pending)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    run_migrations(reset=reset_flag)
