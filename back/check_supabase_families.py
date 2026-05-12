#!/usr/bin/env python3
"""Check Supabase tables for product_family and family data."""
import sys
sys.path.insert(0, '/Users/malo/Documents/Projects/rkllm-server/external/rag/back')

from src.supabase.supabase_client import get_supabase_service

supabase = get_supabase_service()

# Check product_family table
pf_result = supabase.table("product_family").select("count", count="exact").execute()
pf_count = pf_result.count if pf_result.count is not None else 0
print(f"product_family records: {pf_count}")

# Check family table
fam_result = supabase.table("family").select("count", count="exact").execute()
fam_count = fam_result.count if fam_result.count is not None else 0
print(f"family records: {fam_count}")

# Check product table
prod_result = supabase.table("product").select("count", count="exact").execute()
prod_count = prod_result.count if prod_result.count is not None else 0
print(f"product records: {prod_count}")

# Sample some families if they exist
if fam_count > 0:
    fam_sample = supabase.table("family").select("id, code, name").limit(3).execute()
    print(f"\nSample families:")
    for fam in fam_sample.data:
        print(f"  - {fam['code']}: {fam['name']}")

# Sample product_family links if they exist
if pf_count > 0:
    pf_sample = supabase.table("product_family").select("product_id, family_id").limit(3).execute()
    print(f"\nSample product_family links:")
    for link in pf_sample.data:
        print(f"  - product {link['product_id'][:8]}... -> family {link['family_id'][:8]}...")
else:
    print("\nNo product_family links found")
