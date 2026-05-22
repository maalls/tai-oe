#!/usr/bin/env python3
"""
Test script for handle_generate_quote_for_opportunity method.

Tests:
1. Verify opportunity exists
2. Generate quote for opportunity
3. Verify quote document is created
4. Verify quote contains product data

Usage:
    cd /Users/malo/Documents/Projects/rkllm-server/external/rag/back
    python tests/test_generate_quote_for_opportunity.py
"""

import sys
import os
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config import create_database_handler
from src.repository.opportunity import OpportunityRepository

RUN_MANUAL_SMOKE_TESTS = os.getenv("RUN_MANUAL_SMOKE_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MANUAL_SMOKE_TESTS,
    reason="Manual smoke script; set RUN_MANUAL_SMOKE_TESTS=1 to execute against live Supabase data.",
)


def _run_generate_quote_for_opportunity_test() -> bool:
    # Test opportunity ID from user
    opportunity_id = "46b3f829-b7bc-4b6e-9295-3eb219a21476"
    
    print(f"\n{'='*80}")
    print(f"Testing Quote Generation for Opportunity: {opportunity_id}")
    print(f"{'='*80}\n")
    
    # Initialize repository
    repo = OpportunityRepository()
    db_handler = create_database_handler(
        current_file=__file__,
        require_postgres_password=False,
    )
    
    # Step 1: Verify opportunity exists
    print(f"[TEST] Step 1: Verify opportunity exists...")
    try:
        opp_rows = db_handler.execute_dict_query(
            "SELECT * FROM opportunity WHERE id = %s LIMIT 1",
            (opportunity_id,),
        )
        opportunity = opp_rows[0] if opp_rows else None
        if not opportunity:
            print(f"[ERROR] Opportunity not found: {opportunity_id}")
            return False
        
        print(f"[OK] Opportunity found:")
        print(f"     Name: {opportunity.get('name')}")
        print(f"     Source: {opportunity.get('source')}")
        print(f"     Source Reference ID: {opportunity.get('source_reference_id')}")
        print(f"     Status: {opportunity.get('status')}")
        print(f"     Amount: {opportunity.get('amount')}")
        print()
    except Exception as e:
        print(f"[ERROR] Exception while loading opportunity: {e}")
        return False
    
    # Step 2: Check source content availability
    print(f"[TEST] Step 2: Check source content availability...")
    source = opportunity.get('source')
    source_ref_id = opportunity.get('source_reference_id')
    
    if source == 'email':
        try:
            email_rows = db_handler.execute_dict_query(
                "SELECT * FROM email WHERE id = %s LIMIT 1",
                (source_ref_id,),
            )
            if email_rows:
                email = email_rows[0]
                print(f"[OK] Email source found:")
                print(f"     Subject: {email.get('subject')}")
                print(f"     From: {email.get('from_email')}")
                print(f"     Body Preview: {email.get('body_preview', '')[:100]}...")
                
                # Check for attachments
                attachments = db_handler.execute_dict_query(
                    "SELECT * FROM email_attachment WHERE email_id = %s",
                    (source_ref_id,),
                )
                print(f"     Attachments: {len(attachments)}")
                for att in attachments:
                    print(f"        - {att.get('filename')} ({att.get('mime_type')})")
            else:
                # Try lookup by provider_message_id
                email_rows = db_handler.execute_dict_query(
                    "SELECT * FROM email WHERE provider_message_id = %s LIMIT 1",
                    (source_ref_id,),
                )
                if email_rows:
                    email = email_rows[0]
                    print(f"[OK] Email source found (by provider_message_id):")
                    print(f"     Subject: {email.get('subject')}")
                    print(f"     From: {email.get('from_email')}")
                else:
                    print(f"[WARNING] Email source not found for ID: {source_ref_id}")
        except Exception as e:
            print(f"[WARNING] Error checking email source: {e}")
    
    elif source == 'rfp_upload':
        try:
            doc_rows = db_handler.execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (source_ref_id,),
            )
            if doc_rows:
                document = doc_rows[0]
                print(f"[OK] RFP document source found:")
                print(f"     Type: {document.get('type')}")
                print(f"     Storage Key: {document.get('storage_key')}")
                print(f"     Title: {document.get('title')}")
            else:
                print(f"[WARNING] RFP document source not found for ID: {source_ref_id}")
        except Exception as e:
            print(f"[WARNING] Error checking RFP document source: {e}")
    
    elif source == 'text':
        try:
            doc_rows = db_handler.execute_dict_query(
                "SELECT * FROM document WHERE id = %s LIMIT 1",
                (source_ref_id,),
            )
            if doc_rows:
                document = doc_rows[0]
                print(f"[OK] Text document source found:")
                print(f"     Type: {document.get('type')}")
                print(f"     Storage Key: {document.get('storage_key')}")
                print(f"     Title: {document.get('title')}")
                
                # Try to read content from storage
                if document.get('storage_key'):
                    base_storage = Path(__file__).parent.parent / "var" / "storage" / "rfq_sources"
                    file_path = base_storage / document.get('storage_key')
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(f"     Content: {content[:200]}...")
                    else:
                        print(f"[WARNING] Storage file not found: {file_path}")
            else:
                print(f"[WARNING] Text document source not found for ID: {source_ref_id}")
        except Exception as e:
            print(f"[WARNING] Error checking text document source: {e}")
    
    else:
        print(f"[WARNING] Unknown source type: {source}")
    
    print()
    
    # Step 3: Generate quote
    print(f"[TEST] Step 3: Generate quote for opportunity...")
    try:
        result = repo.handle_generate_quote_for_opportunity(opportunity_id=opportunity_id)
        
        if result.get('status') == 'ok':
            print(f"[OK] Quote generation successful!")
            print(f"     Status: {result.get('status')}")
            
            document = result.get('document', {})
            if document:
                print(f"     Document ID: {document.get('id')}")
                print(f"     Title: {document.get('title')}")
                print(f"     Currency: {document.get('currency')}")
                print(f"     PDF Filename: {document.get('pdf_filename')}")
                
                totals = document.get('totals', {})
                print(f"     Total (excl tax): {totals.get('total_excl_tax', 0)}")
                print(f"     Total (incl tax): {totals.get('total_incl_tax', 0)}")
            
            draft = result.get('draft', {})
            if draft:
                print(f"     Draft data available: {bool(draft)}")
                
                # Check if it's a single product or list
                if isinstance(draft, list):
                    print(f"     Products count: {len(draft)}")
                    for idx, product in enumerate(draft[:3]):  # Show first 3 products
                        print(f"        Product {idx+1}:")
                        print(f"           Description: {product.get('description', 'N/A')}")
                        print(f"           Manufacturer: {product.get('manufacturer', 'N/A')}")
                        print(f"           SKU: {product.get('sku', 'N/A')}")
                        print(f"           Quantity: {product.get('quantity', 'N/A')}")
                elif isinstance(draft, dict):
                    products = draft.get('products', [])
                    if products:
                        print(f"     Products count: {len(products)}")
                        for idx, product in enumerate(products[:3]):  # Show first 3 products
                            print(f"        Product {idx+1}:")
                            print(f"           Description: {product.get('description', 'N/A')}")
                            print(f"           Manufacturer: {product.get('manufacturer', 'N/A')}")
                            print(f"           SKU: {product.get('sku', 'N/A')}")
                            print(f"           Quantity: {product.get('quantity', 'N/A')}")
                    else:
                        print(f"     Draft data: {draft}")
            
            print()
            print(f"[SUCCESS] Quote generation completed successfully!")
            return True
        else:
            print(f"[ERROR] Quote generation failed:")
            print(f"     Status: {result.get('status')}")
            print(f"     Message: {result.get('message')}")
            print(f"     Full result: {result}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Exception during quote generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_quote_for_opportunity():
    """Test generating a quote for a specific opportunity."""
    assert _run_generate_quote_for_opportunity_test()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Testing Quote Generation for Opportunity")
    print("="*80)
    
    success = _run_generate_quote_for_opportunity_test()
    
    print("\n" + "="*80)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
