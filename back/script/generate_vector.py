#!/usr/bin/env python3
"""
Generate Qdrant vectors from commerce table.

Queries the fabdis_commerce table and creates a Qdrant collection with
embedding vectors generated from the libelle240 field.

Usage:
    python generate_vector.py [--collection NAME] [--where WHERE] [--limit LIMIT] [--batch-size SIZE]

Examples:
    # Generate vectors for all commerce data
    python generate_vector.py
    
    # Generate for specific collection name
    python generate_vector.py --collection commerce_vectors
    
    # Generate with WHERE clause and limit
    python generate_vector.py --where "tarif > 100" --limit 1000
    
    # Custom batch size for embedding generation
    python generate_vector.py --batch-size 50
"""

import sys
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict
from datetime import date, datetime
from decimal import Decimal

try:
    import yaml
except ImportError:
    yaml = None

from src.controller.db_client import DatabaseHandler
from src.embeddings.embeddings import EmbeddingGenerator
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def get_qdrant_url_from_config() -> str:
    """Load Qdrant URL from config.yml.
    
    Returns:
        Qdrant URL/path from config, or default if not found
    """
    if not yaml:
        return '/rkllm/qdrant_storage'
    
    # Search for config file in standard locations
    config_candidates = [
        Path.cwd() / 'config.yml',
        Path.cwd() / 'back' / 'config.yml',
        Path(__file__).parent.parent / 'config.yml',
        Path(__file__).parent.parent.parent / 'config.yml',
    ]
    
    for config_path in config_candidates:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    qdrant_config = config.get('qdrant', {})
                    url = qdrant_config.get('url')
                    if url:
                        print(f"[Config] Using Qdrant URL from config: {url}")
                        return url
            except Exception as e:
                print(f"[Warning] Could not read config from {config_path}: {e}")
    
    return '/rkllm/qdrant_storage'


def serialize_value(value):
    """Convert non-JSON-serializable values to serializable format."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif value is None:
        return None
    return value


def generate_numeric_id(ref_id: str) -> int:
    """Convert string ID to numeric ID using hash.
    
    Args:
        ref_id: String ID (e.g., refciale)
        
    Returns:
        Numeric ID (positive integer)
    """
    # Create a hash of the string ID
    hash_obj = hashlib.md5(ref_id.encode('utf-8'))
    # Convert to unsigned 64-bit integer (Qdrant uses uint64)
    hash_int = int(hash_obj.hexdigest(), 16) & 0x7FFFFFFFFFFFFFFF  # Keep positive
    return hash_int



def generaxte_vectors_from_commerce(
    collection_name: str = 'commerce_vectors',
    where_clause: str = None,
    limit: int = None,
    batch_size: int = 100,
    qdrant_path: str = None
):
    """Generate vectors from commerce table and insert into Qdrant.
    
    Args:
        collection_name: Qdrant collection name
        where_clause: Optional WHERE clause for filtering
        limit: Maximum number of rows to process
        batch_size: Batch size for embedding generation
        qdrant_path: Path or URL to Qdrant storage
    """
    # Initialize components
    print("Initializing database connection...")
    db = DatabaseHandler()
    print("Initializing embedding generator...")
    embedding_gen = EmbeddingGenerator()
    # Initialize Qdrant client (URL or file path)
    client = createQudrantClient(qdrant_path)
    # Create collection
    create_collection(client, collection_name, embedding_gen.vector_size)
    
    # Execute query
    try:
        payloads = get_products(db, limit)
        total_payload = len(payloads)
        print(f"Retrieved {total_payload} payload from database")
    except Exception as e:
        print(f"❌ Error executing query: {e}", file=sys.stderr)
        sys.exit(1)
    
    if total_payload == 0:
        print("No payload to process. Exiting.")
        return
    
    # Process in batches
    print(f"\nGenerating embeddings and inserting into Qdrant (batch size: {batch_size})...")
    
    points_inserted = 0
    for i in range(0, total_payload, batch_size):
        batch = payloads[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_payload + batch_size - 1) // batch_size
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} rows)...")
        
        # Extract texts for embedding
        texts = []
        for payload in batch:
            #libelle = row.get('libelle240', '') or ''
            # Can add more fields to improve embeddings
            # e.g., designation = row.get('designation', '') or ''
            # text = f"{libelle} {designation}"
            texts.append(payload['vector_text'])
        
        # Generate embeddings in batch
        try:
            embeddings = embedding_gen.embed_batch(texts)
        except Exception as e:
            print(f"❌ Error generating embeddings for batch {batch_num}: {e}")
            continue
        
        # Prepare points
        points = []
        for idx, (row, embedding) in enumerate(zip(batch, embeddings)):
            # Get refciale and convert to numeric ID
            original_id = str(row['marque'] + "-" + row['refciale'])
            point_id = generate_numeric_id(original_id)
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=row
                )
            )
        
        # Insert batch into Qdrant
        try:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            points_inserted += len(points)
            print(f"  ✓ Inserted {len(points)} points ({points_inserted}/{total_payload} total)")
        except Exception as e:
            print(f"  ❌ Error inserting batch {batch_num}: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ Completed!")
    print(f"   Collection: {collection_name}")
    print(f"   Total points inserted: {points_inserted}/{total_payload}")
    print(f"   Vector dimension: {embedding_gen.vector_size}")
    print(f"{'='*60}")
    
    # Get collection info
    try:
        info = client.get_collection(collection_name)
        print(f"\nCollection statistics:")
        print(f"   Points count: {info.points_count}")
        print(f"   Vectors count: {info.vectors_count}")
    except Exception as e:
        print(f"Warning: Could not retrieve collection info: {e}")



def get_products(db, limit = None) -> List[Dict]:

    query = "SELECT * FROM fabdis_commerce"
    if limit:
        query += f" LIMIT {limit}"

    rows = db.execute_dict_query(query)
    total_rows = len(rows)
    payloads = []
    i = 0
    for row in rows:
        i+=1
        print("Processing row with refciale:", i, total_rows)
        payload = get_product(row, db)
        payloads.append(payload)
    return payloads
        
        # collect related etim information
def get_product(row, db):
    family_codes = []
    for key in ("mkt1", "mkt2", "mkt3", "mkt4", "mkt5"):
        value = row.get(key)
        if isinstance(value, str):
            code = value.strip()
            if code:
                family_codes.append(code)
        elif value is not None:
            family_codes.append(str(value))
    payload = {
        'marque': row.get('marque'),
        'refciale': row.get('refciale'),
        'libelle240': row.get('libelle240'),
        'tarif': row.get('tarif'),
        'family_codes': family_codes
    }
    refciale = row.get('refciale')
    if not row.get('refciale') or not row.get('marque'):
        raise ValueError("Row missing 'refciale' or 'marque' field")
    
    etim_query = f"""
        SELECT e.*
        FROM fabdis_etim e
        JOIN fabdis_commerce c ON e.refciale = c.refciale and e.marque = c.marque 
        WHERE c.refciale = '{refciale}'
    """
    etim_rows = db.execute_dict_query(etim_query)
    etim_payload = {}
    for row in etim_rows:
        etim_payload[row["featuredesc"]] = row["valuedesc"]

    payload['etim'] = etim_payload

    payload['vector_text'] = f"{payload['libelle240']} " + " ".join([f"{k}: {v}" for k, v in etim_payload.items()])

    return payload

def createQudrantClient(qdrant_path: str = None) -> QdrantClient:
    """Create Qdrant client from path or URL.
    
    Args:
        qdrant_path: Path or URL to Qdrant storage
    Returns:
        QdrantClient instance
    """
    if qdrant_path is None:
        raise ValueError("Qdrant path or URL must be provided")
    
    if qdrant_path.startswith('http://') or qdrant_path.startswith('https://'):
        # Remote Qdrant server
        client = QdrantClient(url=qdrant_path)
    else:
        # Local Qdrant storage
        client = QdrantClient(path=qdrant_path)

    return client 

def create_collection(client: QdrantClient, collection_name: str, vector_size: int = 384):
    """Create or recreate Qdrant collection.
    
    Args:
        client: Qdrant client
        collection_name: Name of the collection to create
        vector_size: Embedding vector dimension
    """
    # Check if collection exists
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if collection_name in collection_names:
        print(f"⚠️  Collection '{collection_name}' already exists")
        response = input("Do you want to recreate it? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Aborting. Use existing collection or choose a different name.")
            sys.exit(0)
        
        print(f"Deleting existing collection '{collection_name}'...")
        client.delete_collection(collection_name)
    
    print(f"Creating collection '{collection_name}' with vector size {vector_size}...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )
    print(f"✓ Collection '{collection_name}' created")


def main():
    # Get default Qdrant path from config
    default_qdrant_path = get_qdrant_url_from_config()
    
    parser = argparse.ArgumentParser(
        description='Generate Qdrant vectors from commerce table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--collection', '-c',
        default='commerce_vectors',
        help='Qdrant collection name (default: commerce_vectors)'
    )
    
    parser.add_argument(
        '--where', '-w',
        help='WHERE clause for filtering rows (e.g., "tarif > 100")'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Maximum number of rows to process'
    )
    
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Batch size for embedding generation (default: 100)'
    )
    
    parser.add_argument(
        '--qdrant-path', '-p',
        default=default_qdrant_path,
        help=f'Path to Qdrant storage (default: {default_qdrant_path})'
    )
    
    args = parser.parse_args()
    
    try:
        generate_vectors_from_commerce(
            collection_name=args.collection,
            where_clause=args.where,
            limit=args.limit,
            batch_size=args.batch_size,
            qdrant_path=args.qdrant_path
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Process cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
