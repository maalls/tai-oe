#!/usr/bin/env python3
"""Apply email auth migrations using Supabase SQL editor simulation."""

from pathlib import Path
from src.supabase import get_supabase_service

def apply_migrations_directly():
    """Apply auth migrations by reading SQL files and using PostgreSQL directly."""
    
    supabase = get_supabase_service()
    
    # Read migration files
    migrations_dir = Path(__file__).parent / "migrations"
    
    migration_files = [
        "007_add_email_auth_fields.sql",
        "008_create_sender_verification_table.sql"
    ]
    
    print("\n" + "="*60)
    print("📧 Applying Email Auth Migrations")
    print("="*60 + "\n")
    
    all_sql = ""
    for mig_file in migration_files:
        sql_path = migrations_dir / mig_file
        if sql_path.exists():
            print(f"📄 Reading {mig_file}...")
            all_sql += "\n" + sql_path.read_text()
            print(f"   ✓ Loaded {len(sql_path.read_text())} bytes")
    
    # Try to execute via Supabase
    try:
        print("\n⏳ Attempting Supabase SQL execution...")
        
        # Use the SQL editor endpoint
        headers = {
            "Authorization": f"Bearer {supabase.auth.get_session().access_token if supabase.auth.get_session() else ''}",
            "Content-Type": "application/json"
        }
        
        # Actually, let's use psycopg2 to connect directly
        import psycopg2
        from os import environ
        
        db_url = environ.get('SUPABASE_DB_URL') or environ.get('DATABASE_URL')
        
        if not db_url:
            print("❌ No database URL found. Please set SUPABASE_DB_URL or DATABASE_URL")
            return False
        
        print(f"✓ Connecting to database...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute all SQL
        cursor.execute(all_sql)
        conn.commit()
        
        print("✅ All migrations applied successfully!")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Manual fix: Run this SQL in Supabase SQL Editor:")
        print(all_sql)
        return False

if __name__ == "__main__":
    apply_migrations_directly()
    print("\n" + "="*60 + "\n")
