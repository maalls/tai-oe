#!/usr/bin/env python3
"""Quick test to sample refciales from different parts of Qdrant collection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.controller.qdrant_handler import QdrantHandler

qdrant = QdrantHandler()
print('Sampling refciales from different sections of Qdrant...\n')

refciales = set()

# Sample from different parts of the collection  
for which, offset in [('first 100', 0), ('offset 10k', 10000), ('offset 100k', 100000), ('offset 250k', 250000)]:
    try:
        points, _ = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        batch_refs = []
        for point in points:
            payload = point.payload if hasattr(point, 'payload') else {}
            ref = payload.get('refciale', '').strip() if payload else ''
            if ref:
                batch_refs.append(ref)
                refciales.add(ref)
        
        print(f'{which}: {len(batch_refs)}/100 points have refciale')
        if batch_refs:
            print(f'  Examples: {batch_refs[:3]}')
    except Exception as e:
        print(f'{which}: Error - {e}')

print(f'\nTotal unique refciales found across samples: {len(refciales)}')
if refciales:
    print(f'Examples: {list(refciales)[:10]}')
