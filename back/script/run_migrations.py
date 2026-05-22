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
from src.infrastructure.config import create_database_handler
from src.infrastructure.config import create_database_service

BACK_DIR = Path(__file__).resolve().parents[1]


def _build_database_service_for_migrations():
    return create_database_service(
        current_file=str(Path(__file__).resolve()),
        require_postgres_password=False,
    )


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


def get_executed_migrations(db_handler) -> set:
    """Get list of migrations that have already been executed."""
    try:
        rows = db_handler.execute_dict_query("SELECT migration_name FROM migrations")
        return {row["migration_name"] for row in rows} if rows else set()
    except Exception as e:
        print(f"Error fetching executed migrations: {e}")
        print("Note: If migrations table doesn't exist, run schema/migrations.sql first")
        return set()


def get_migration_db_url() -> tuple[str, str]:
    """Resolve the PostgreSQL URL used for schema migrations."""
    service = _build_database_service_for_migrations()
    return service.resolve_migration_db_url()


def get_db_connection():
    """Get direct PostgreSQL connection with admin privileges."""
    service = _build_database_service_for_migrations()
    source, masked_db_url = service.resolve_masked_migration_db_url()
    print(f"ℹ Connecting to database with {source}: {masked_db_url}")

    conn = service.create_migration_db()
    try:
        service.assert_migration_create_privilege(conn)
    except Exception:
        conn.close()
        raise

    return conn


def execute_migration(db_handler, migration: Dict[str, str], auto_confirm: bool = False) -> bool:
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
        db_handler.execute_update(
            "INSERT INTO migrations (migration_name, checksum) VALUES (%s, %s)",
            (migration["name"], migration["checksum"]),
        )
        
        print(f"✓ Migration executed and recorded: {migration['name']}")
        return True
        
    except Exception as e:
        print(f"✗ Error executing migration {migration['name']}: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_migration(db_handler, migration_name: str):
    """Remove a migration record to allow re-execution."""
    try:
        db_handler.execute_update(
            "DELETE FROM migrations WHERE migration_name = %s",
            (migration_name,),
        )
        print(f"✓ Removed migration record: {migration_name}")
    except Exception as e:
        print(f"✗ Error removing migration record: {e}")


def run_migrations(reset: bool = False):
    """Run all pending migrations."""
    print("Starting migration process...")
    
    db_handler = create_database_handler(
        current_file=__file__,
        require_postgres_password=False,
    )
    
    # Get all migration files
    migration_files = get_migration_files()
    if not migration_files:
        print("No migration files found.")
        return
    
    print(f"Found {len(migration_files)} migration file(s)")
    
    # Get already executed migrations
    executed = get_executed_migrations(db_handler)
    print(f"Already executed: {len(executed)} migration(s)")
    
    # Reset if requested
    if reset and executed:
        print("\n⚠ RESET MODE: Clearing migration records...")
        for migration_name in executed:
            reset_migration(db_handler, migration_name)
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
        if execute_migration(db_handler, migration):
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
