#!/usr/bin/env python3
"""
Script to clear all data from email, opportunity, contact, and account tables.

CAUTION: This will permanently delete all data from these tables!
Use only for development/testing.

Order matters due to foreign key constraints:
1. email (may reference opportunity)
2. opportunity (references account)
3. contact (references account)
4. account (no dependencies)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.supabase import get_supabase_service


def clear_tables():
    """Clear all data from tables in correct order."""
    supabase = get_supabase_service()
    
    tables = [
        ('email', 'email table'),
        ('opportunity', 'opportunity table'),
        ('contact', 'contact table'),
        ('account', 'account table'),
    ]
    
    print("⚠️  WARNING: This will delete ALL data from the following tables:")
    for table, desc in tables:
        print(f"  - {desc}")
    
    confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
    if confirm != 'yes':
        print("❌ Cancelled")
        return
    
    for table, desc in tables:
        try:
            print(f"🗑️  Deleting all rows from {desc}...", end=' ', flush=True)
            
            # Get count before deletion
            count_response = supabase.table(table).select("id", count="exact").execute()
            count = count_response.count if hasattr(count_response, 'count') else 0
            
            if count > 0:
                # Delete all rows - use a column that exists and check not.is.null
                # The proper syntax is .is_(column, 'not_null')
                first_row_response = supabase.table(table).select("id").limit(1).execute()
                if first_row_response.data:
                    supabase.table(table).delete().is_("id", "not_null").execute()
            
            print(f"✓ Deleted {count} rows")
            
        except Exception as e:
            print(f"❌ Error deleting from {table}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    print("\n✅ All tables cleared successfully")


if __name__ == '__main__':
    clear_tables()
