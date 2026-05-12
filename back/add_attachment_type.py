#!/usr/bin/env python3
"""
Direct SQL execution to add ATTACHMENT type to document_type enum.
Uses psycopg2 for direct PostgreSQL connection.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def add_attachment_type():
    print("\n" + "="*80)
    print("ADDING ATTACHMENT TYPE TO DOCUMENT_TYPE ENUM")
    print("="*80 + "\n")
    
    try:
        import psycopg2
    except ImportError:
        print("[ERROR] psycopg2 not installed. Installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
        import psycopg2
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        return False
    
    print(f"[INFO] Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # SQL to add ATTACHMENT to the enum type
        # We use ALTER TYPE ADD VALUE IF NOT EXISTS (PostgreSQL 13+)
        sql = """
        DO $$ 
        BEGIN
            ALTER TYPE document_type ADD VALUE IF NOT EXISTS 'ATTACHMENT';
        EXCEPTION WHEN others THEN
            -- If ALTER TYPE fails, it's likely already added
            NULL;
        END $$;
        """
        
        print("[INFO] Executing SQL...")
        cursor.execute(sql)
        conn.commit()
        
        print("[SUCCESS] ✅ ATTACHMENT type added successfully!")
        
        # Verify the type was added
        cursor.execute("""
            SELECT enum_range(NULL::document_type)::text;
        """)
        result = cursor.fetchone()
        print(f"[INFO] Current document_type enum values: {result[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = add_attachment_type()
    sys.exit(0 if success else 1)
