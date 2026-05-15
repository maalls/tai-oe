#!/usr/bin/env python3
"""Check if Qdrant scroll returns unique point IDs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.controller.qdrant_handler import QdrantHandler

qdrant = QdrantHandler()
print('Checking point uniqueness across scroll batches...\n')

all_ids = set()
all_refciales = set()
offset = 0
batch_count = 0

# Check first 20 batches
for batch_num in range(20):
    try:
        points, _ = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        batch_ids = []
        batch_refs = []
        for point in points:
            all_ids.add(point.id)
            batch_ids.append(point.id)
            
            ref = point.payload.get('refciale', '') if point.payload else ''
            if ref:
                all_refciales.add(ref)
                batch_refs.append(ref)
        
        print(f'Batch {batch_num + 1} (offset {offset}):')
        print(f'  Points: {len(points)}')
        print(f'  Unique IDs in batch: {len(set(batch_ids))}')
        print(f'  Unique refciales in batch: {len(set(batch_refs))}')
        print(f'  Example IDs: {batch_ids[:3]}')
        print(f'  Example refciales: {batch_refs[:3]}')
        print()
        
        offset += len(points)
        batch_count += 1
        
        if len(points) == 0:
            break
            
    except Exception as e:
        print(f'Error at batch {batch_num}: {e}')
        break

print(f'\nSummary across {batch_count} batches:')
print(f'  Total unique point IDs: {len(all_ids)}')
print(f'  Total unique refciales: {len(all_refciales)}')
print(f'  Points processed: {offset}')
print(f'  Average refciales per 100 points: {len(all_refciales) / batch_count:.1f}')
