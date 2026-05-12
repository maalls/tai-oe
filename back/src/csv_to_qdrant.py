#!/usr/bin/env python3
"""
Export CSV files to Qdrant vector database collections.

Each CSV row becomes a document in Qdrant with:
- Vector embedding from concatenated text columns
- All CSV columns as metadata/payload
- Support for custom text column selection
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

from qdrant_client_wrapper import VectorDBClient
from embeddings import EmbeddingGenerator


def csv_to_qdrant(
    csv_file: str,
    collection_name: str = None,
    text_columns: List[str] = None,
    qdrant_url: str = None,
    batch_size: int = 100,
    limit_rows: int = None
) -> bool:
    """
    Export CSV file to Qdrant collection.
    
    Args:
        csv_file: Path to CSV file
        collection_name: Qdrant collection name (default: csv filename without extension)
        text_columns: Columns to use for embedding (default: all text columns)
        qdrant_url: Qdrant server URL (default: QDRANT_URL env var or local storage)
        batch_size: Number of rows to process per batch (default: 100)
        limit_rows: Maximum rows to import (default: all rows)
    
    Returns:
        True if successful
    """
    csv_path = Path(csv_file).resolve()
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return False
    
    # Default collection name from filename
    if collection_name is None:
        collection_name = csv_path.stem.lower().replace(' ', '_').replace('-', '_')
    
    print(f"\n{'='*60}")
    print(f"CSV to Qdrant Export")
    print(f"{'='*60}")
    print(f"CSV File: {csv_path}")
    print(f"Collection: {collection_name}")
    print(f"Qdrant URL: {qdrant_url or os.getenv('QDRANT_URL', 'local storage')}")
    print(f"{'='*60}\n")
    
    # Initialize clients
    try:
        client = VectorDBClient(url=qdrant_url, collection_name=collection_name)
        embedder = EmbeddingGenerator()
    except Exception as e:
        print(f"Error initializing clients: {e}")
        return False
    
    # Create collection
    if not client.create_collection():
        print("Error: Failed to create collection")
        return False
    
    # Read CSV and prepare data
    try:
        with csv_path.open('r', encoding='utf-8', errors='replace', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                print("Error: CSV has no headers")
                return False
            
            print(f"CSV Headers: {', '.join(headers)}")
            
            # Determine text columns for embedding
            if text_columns is None:
                # Use all columns by default
                text_columns = list(headers)
            else:
                # Validate specified columns exist
                missing = set(text_columns) - set(headers)
                if missing:
                    print(f"Warning: Text columns not found in CSV: {missing}")
                text_columns = [c for c in text_columns if c in headers]
            
            print(f"Embedding columns: {', '.join(text_columns)}\n")
            
            # Process rows in batches
            points = []
            row_count = 0
            total_inserted = 0
            
            for row_idx, row in enumerate(reader):
                if limit_rows and row_idx >= limit_rows:
                    break
                
                # Generate text for embedding
                text_parts = [str(row.get(col, '')).strip() for col in text_columns]
                text = ' '.join(filter(None, text_parts))
                
                if not text:
                    continue  # Skip empty rows
                
                # Generate embedding
                vector = embedder.embed_text(text)
                
                # Create payload with all CSV columns
                payload = {k: v for k, v in row.items()}
                
                # Add metadata
                payload['_source_file'] = csv_path.name
                payload['_row_index'] = row_idx
                payload['_text'] = text[:500]  # Store first 500 chars of text
                
                # Generate unique ID from row content
                row_hash = hashlib.md5(f"{csv_path.name}:{row_idx}".encode()).hexdigest()
                point_id = int(row_hash[:8], 16) % (2**31)
                
                from qdrant_client.models import PointStruct
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
                points.append(point)
                row_count += 1
                
                # Insert batch when full
                if len(points) >= batch_size:
                    try:
                        client.client.upsert(
                            collection_name=collection_name,
                            points=points
                        )
                        total_inserted += len(points)
                        print(f"  ✓ Inserted batch ({total_inserted} total)")
                        points = []
                    except Exception as e:
                        print(f"  ✗ Error inserting batch: {e}")
                        return False
            
            # Insert remaining points
            if points:
                try:
                    client.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    total_inserted += len(points)
                    print(f"  ✓ Inserted final batch ({total_inserted} total)")
                except Exception as e:
                    print(f"  ✗ Error inserting final batch: {e}")
                    return False
            
            print(f"\n{'='*60}")
            print(f"✓ Successfully exported {total_inserted} rows to collection '{collection_name}'")
            print(f"{'='*60}\n")
            return True
            
    except Exception as e:
        print(f"Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Export CSV files to Qdrant vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export entire CSV
  python csv_to_qdrant.py data.csv
  
  # Custom collection name
  python csv_to_qdrant.py data.csv --collection my_collection
  
  # Use specific columns for embedding
  python csv_to_qdrant.py data.csv --text-columns name description
  
  # Remote Qdrant server
  python csv_to_qdrant.py data.csv --url http://localhost:6333
  
  # Limit to first 1000 rows
  python csv_to_qdrant.py data.csv --limit 1000
        """
    )
    
    parser.add_argument('csv_file', help='CSV file to export')
    parser.add_argument('--collection', '-c', help='Qdrant collection name (default: CSV filename)')
    parser.add_argument('--text-columns', '-t', nargs='+', help='Columns to use for embedding (default: all)')
    parser.add_argument('--url', '-u', help='Qdrant server URL (default: QDRANT_URL env or local)')
    parser.add_argument('--batch-size', '-b', type=int, default=100, help='Batch size (default: 100)')
    parser.add_argument('--limit', '-l', type=int, help='Max rows to import (default: all)')
    
    args = parser.parse_args()
    
    success = csv_to_qdrant(
        csv_file=args.csv_file,
        collection_name=args.collection,
        text_columns=args.text_columns,
        qdrant_url=args.url,
        batch_size=args.batch_size,
        limit_rows=args.limit
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
