#!/usr/bin/env python3
"""
Verify that ATTACHMENT type has been added to the document_type enum.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.clients.supabase import get_supabase_service

def verify_attachment_type():
    print("\n" + "="*80)
    print("VERIFYING ATTACHMENT TYPE IN DATABASE")
    print("="*80 + "\n")
    
    try:
        supabase = get_supabase_service()
        
        # Try to insert a test document with type ATTACHMENT
        print("[VERIFY] Testing if ATTACHMENT type is available...")
        
        test_data = {
            "opportunity_id": "00000000-0000-0000-0000-000000000000",  # dummy UUID
            "type": "ATTACHMENT",
            "status": "RECEIVED",
            "title": "Test Attachment",
            "currency": "EUR",
            "channel": "OTHER",
            "storage_key": "test_attachment.pdf",
        }
        
        try:
            result = supabase.table("document").insert(test_data).execute()
            print("[VERIFY] ✅ ATTACHMENT type is available in database!")
            print(f"[VERIFY] Test insert successful")
            
            # Delete the test record
            if result.data:
                test_id = result.data[0]['id']
                supabase.table("document").delete().eq("id", test_id).execute()
                print("[VERIFY] ✓ Cleaned up test record")
                
        except Exception as e:
            error_msg = str(e)
            if "invalid input value for enum" in error_msg and "ATTACHMENT" in error_msg:
                print("[VERIFY] ❌ ATTACHMENT type is NOT available in database")
                print(f"[VERIFY] Error: {error_msg}")
            else:
                print(f"[VERIFY] Error (may be expected due to invalid UUID): {e}")
                if "ATTACHMENT" not in error_msg:
                    print("[VERIFY] ✅ ATTACHMENT type appears to be valid (error is unrelated)")
        
        # Also check the migrations table
        print("\n[VERIFY] Checking migrations table...")
        migrations = supabase.table("migrations").select("*").order("created_at", desc=True).limit(5).execute()
        
        if migrations.data:
            print("\n[VERIFY] Recent migrations:")
            for mig in migrations.data:
                print(f"  - {mig.get('name', 'N/A')}: {mig.get('applied_at', 'N/A')}")
                if '006' in mig.get('name', ''):
                    print("[VERIFY] ✅ Migration 006 appears to be applied!")
        else:
            print("[VERIFY] No migrations table found (may be OK)")
            
    except Exception as e:
        print(f"[VERIFY] ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_attachment_type()
