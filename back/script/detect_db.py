"""
Detect and test database connection for migrations.
"""
import os
import psycopg2
from src.infrastructure.runtime.env_loader import load_runtime_env

load_runtime_env(current_file=__file__)


def try_connection(connection_string, description):
    """Try to connect with a given connection string."""
    print(f"\nTrying {description}:")
    print(f"  {connection_string}")
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"  ✓ SUCCESS! PostgreSQL version: {version[0][:50]}...")
        return connection_string
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None


def main():
    print("=" * 60)
    print("DATABASE CONNECTION DETECTOR")
    print("=" * 60)
    
    # Try different connection strings
    possibilities = [
        (os.getenv('DATABASE_URL'), "DATABASE_URL from .env"),
        ("postgresql://postgres:postgres@localhost:54322/postgres", "Local Supabase default (port 54322)"),
        ("postgresql://postgres:postgres@127.0.0.1:54322/postgres", "Local Supabase 127.0.0.1 (port 54322)"),
        ("postgresql://postgres:postgres@localhost:5432/postgres", "Standard PostgreSQL (port 5432)"),
        ("postgresql://postgres:postgres@127.0.0.1:5432/postgres", "Standard PostgreSQL 127.0.0.1 (port 5432)"),
    ]
    
    working_connection = None
    
    for conn_str, desc in possibilities:
        if conn_str:
            result = try_connection(conn_str, desc)
            if result:
                working_connection = result
                break
    
    print("\n" + "=" * 60)
    if working_connection:
        print("FOUND WORKING CONNECTION!")
        print("=" * 60)
        print(f"\nAdd this to your .env file:")
        print(f"DATABASE_URL={working_connection}")
        print("\nOr run migrations with this connection string.")
    else:
        print("NO WORKING CONNECTION FOUND")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Make sure your Supabase instance is running")
        print("2. Check 'docker ps' to see if postgres is running")
        print("3. Look for the database port in your docker-compose.yml")
        print("4. Or use the Supabase SQL Editor at http://localhost:8003")


if __name__ == "__main__":
    main()
