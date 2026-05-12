"""
Quick script to run SQL migrations on Supabase.
"""
import sys
import os
from pathlib import Path
from src.supabase.supabase_client import get_supabase_service
import requests
from dotenv import load_dotenv

load_dotenv()

def run_migration(migration_file=None):
    """Run a SQL migration file."""
    # Determine which migration to run
    if migration_file:
        # Strip migrations/ prefix if provided
        migration_file = migration_file.replace("migrations/", "").replace("migrations\\", "")
        migration_path = Path("migrations") / migration_file
    else:
        # Find the latest migration
        migrations_dir = Path("migrations")
        migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
        if not migration_files:
            print("No migration files found in migrations/")
            return
        migration_path = migration_files[-1]
    
    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return
    
    # Read the SQL file
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    print(f"Running migration: {migration_path.name}")
    print("-" * 60)
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return
    
    
    # Use PostgREST to execute raw SQL via a workaround
    # We'll use the query endpoint directly
    try:
        # Use Supabase PostgREST's query interface
        supabase = get_supabase_service()

        # If SQL contains a DO block, execute the whole script via psycopg2
        if "DO $$" in sql or "DO $" in sql:
            execute_with_psycopg2(sql)
            try:
                supabase.table("migrations").insert({
                    "migration_name": migration_path.name,
                    "executed_at": __import__('datetime').datetime.utcnow().isoformat(),
                }).execute()
                print(f"✓ Recorded migration: {migration_path.name}")
            except Exception as record_error:
                print(f"⚠ Could not record migration (table may not exist): {record_error}")
            print("\n✓ Migration completed successfully!")
            return
        
        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                # Execute via direct HTTP request to PostgREST
                url = f"{supabase_url}/rest/v1/rpc/query"
                headers = {
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json'
                }
                
                # Try executing as RPC first
                try:
                    result = supabase.rpc('query', {'sql': statement}).execute()
                    print(f"✓ Executed: {statement[:60]}...")
                except Exception as rpc_error:
                    # If RPC doesn't work, execute using psycopg2 directly
                    print(f"⚠ RPC failed, trying direct PostgreSQL connection...")
                    execute_with_psycopg2(statement)
        
        # Record migration in migrations table
        try:
            supabase.table("migrations").insert({
                "migration_name": migration_path.name,
                "executed_at": __import__('datetime').datetime.utcnow().isoformat(),
            }).execute()
            print(f"✓ Recorded migration: {migration_path.name}")
        except Exception as record_error:
            print(f"⚠ Could not record migration (table may not exist): {record_error}")
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"⚠ Error: {e}")
        print("\nPlease run this SQL manually in Supabase SQL Editor:")
        print("=" * 60)
        print(sql)
        print("=" * 60)

def execute_with_psycopg2(sql):
    """Execute SQL using direct PostgreSQL connection."""
    try:
        import psycopg2
        
        # Get database connection string
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise Exception("DATABASE_URL not set")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Executed via PostgreSQL: {sql[:60]}...")
        
    except ImportError:
        raise Exception("psycopg2 not installed. Run: pip install psycopg2-binary")
    except Exception as e:
        raise Exception(f"PostgreSQL execution failed: {e}")

if __name__ == "__main__":
    migration_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_migration(migration_file)
