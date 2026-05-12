#!/usr/bin/env python3
"""Check the current state of contact and account tables."""

import os
import sys
from pathlib import Path

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
    sys.exit(1)

from supabase import create_client

def main():
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Get account count
    try:
        acc_response = supabase.table('account').select('id').execute()
        accounts = acc_response.data or []
        print(f"Total accounts in database: {len(accounts)}")
        if len(accounts) <= 10:
            for acc in accounts:
                print(f"  - {acc.get('id', 'N/A')[:8]}...")
    except Exception as e:
        print(f"Error querying accounts: {e}")
    
    # Get contact count
    try:
        contact_response = supabase.table('contact').select('id, name, email, user_id, created_at').order('created_at', { 'ascending': False }).limit(10).execute()
        contacts = contact_response.data or []
        print(f"\nLatest 10 contacts in database:")
        for contact in contacts:
            print(f"  - {contact.get('name', 'N/A')} ({contact.get('email', 'N/A')}) [user: {str(contact.get('user_id', 'N/A'))[:8]}...]")
    except Exception as e:
        print(f"Error querying contacts: {e}")

if __name__ == '__main__':
    main()
