#!/usr/bin/env python3
"""Test the refciale extraction logic from the cleanup script."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.controller.qdrant_handler import QdrantHandler

qdrant = QdrantHandler()
print('Testing refciale extraction logic...\n')

points, _ = qdrant.client.scroll(
    collection_name=qdrant.collection_name,
    limit=25,
    offset=0,
    with_payload=True,
    with_vectors=False
)

refciales = set()
errors = 0

for i, point in enumerate(points[:5]):
    print(f'Point {i}:')
    print(f'  type(point): {type(point).__name__}')
    print(f'  hasattr(point, "payload"): {hasattr(point, "payload")}')
    
    try:
        # Use exact logic from cleanup script
        payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
        print(f'  payload type: {type(payload).__name__}')
        print(f'  isinstance(payload, dict): {isinstance(payload, dict)}')
        
        refciale = payload.get('refciale', '').strip() if isinstance(payload, dict) else ''
        print(f'  refciale: {repr(refciale)}')
        
        if refciale:
            refciales.add(refciale)
            print(f'  ✓ Added to set')
        else:
            print(f'  ✗ Empty, skipped')
    except Exception as e:
        errors += 1
        print(f'  ✗ Exception: {e}')
    print()

print(f'\nSummary:')
print(f'  Points processed: 5')
print(f'  Refciales extracted: {len(refciales)}')
print(f'  Exceptions: {errors}')
print(f'  Examples: {list(refciales)[:10]}')

# Now test with full batch
print(f'\n\nTesting with full batch of {len(points)} points:')

refciales_full = set()
errors_full = 0

for point in points:
    try:
        payload = point.payload if hasattr(point, 'payload') else point.get('payload', {})
        refciale = payload.get('refciale', '').strip() if isinstance(payload, dict) else ''
        if refciale:
            refciales_full.add(refciale)
        else:
            errors_full += 1
    except Exception as e:
        errors_full += 1

print(f'  Total points: {len(points)}')
print(f'  Unique refciales: {len(refciales_full)}')
print(f'  Empty/Error: {errors_full}')
print(f'  Examples: {list(refciales_full)[:10]}')
