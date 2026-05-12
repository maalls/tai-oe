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
from src.supabase.supabase_client import get_supabase_service
import psycopg2
from dotenv import load_dotenv

load_dotenv()


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


def get_db_connection():
    """Get direct PostgreSQL connection with admin privileges."""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        raise ValueError(
            "DATABASE_URL not set in .env file. "
            "Add: DATABASE_URL=postgresql://<admin_user>:<password>@localhost:5432/postgres"
        )
    
    print(f"ℹ Connecting to database with admin credentials...")
    return psycopg2.connect(db_url)


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
