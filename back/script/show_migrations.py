"""
Run migrations directly via Supabase SQL Editor.
Copies SQL to clipboard for easy pasting.
"""
from pathlib import Path
import subprocess


def main():
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        print("No migrations directory found.")
        return
    
    print("=" * 60)
    print("MIGRATIONS TO RUN IN SUPABASE SQL EDITOR")
    print("=" * 60)
    print(f"\nGo to: http://localhost:8003/project/default/sql\n")
    
    sql_parts = []
    
    for migration_file in sorted(migrations_dir.glob("*.sql")):
        print(f"\n{'=' * 60}")
        print(f"Migration: {migration_file.name}")
        print(f"{'=' * 60}")
        
        content = migration_file.read_text()
        print(content)
        sql_parts.append(f"-- {migration_file.name}")
        sql_parts.append(content)
        sql_parts.append("")
    
    # Combine all SQL
    full_sql = "\n".join(sql_parts)
    
    print(f"\n{'=' * 60}")
    print("COMBINED SQL (copied to clipboard)")
    print(f"{'=' * 60}\n")
    
    # Try to copy to clipboard
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(full_sql.encode('utf-8'))
        print("✓ SQL copied to clipboard! Paste it in Supabase SQL Editor.")
    except Exception as e:
        print(f"Could not copy to clipboard: {e}")
        print("\nCopy this SQL manually:\n")
        print(full_sql)


if __name__ == "__main__":
    main()
