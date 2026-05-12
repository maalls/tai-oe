#!/usr/bin/env python3
"""Test script for QdrantHandler."""

import sys
from pathlib import Path

from src.controller.qdrant_handler import QdrantHandler


def test_qdrant_handler():
    """Test basic QdrantHandler functionality."""
    
    print("=" * 60)
    print("Testing QdrantHandler")
    print("=" * 60)
    
    # Initialize handler
    print("\n1. Initializing QdrantHandler...")
    try:
        handler = QdrantHandler()
        print(f"   ✓ Handler initialized")
        print(f"   - URL: {handler.url}")
        print(f"   - Collection: {handler.collection_name}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test connection
    print("\n2. Testing connection...")
    if handler.test_connection():
        print("   ✓ Connection successful")
    else:
        print("   ✗ Connection failed")
        return False
    
    # List collections
    print("\n3. Listing collections...")
    collections = handler.get_collections()
    print(f"   Found {len(collections)} collections:")
    for coll in collections:
        print(f"   - {coll}")
    
    # Get collection info
    if collections:
        print("\n4. Getting collection info...")
        for coll_name in collections[:3]:  # Check first 3
            info = handler.get_collection_info(coll_name)
            if info:
                print(f"   Collection: {coll_name}")
                print(f"     Points: {info.get('points_count', 0)}")
                print(f"     Status: {info.get('status', 'unknown')}")
                print(f"     Vector size: {info.get('vector_size', 'N/A')}")
    
    # Test scroll (if default collection exists)
    print(f"\n5. Testing scroll on '{handler.collection_name}'...")
    result = handler.scroll_points(limit=5, with_payload=True, with_vectors=False)
    if 'error' in result:
        print(f"   Note: {result['error']}")
    else:
        print(f"   ✓ Retrieved {result['count']} points")
        if result['points']:
            print(f"   Sample point ID: {result['points'][0].get('id')}")
            if 'payload' in result['points'][0]:
                keys = list(result['points'][0]['payload'].keys())[:5]
                print(f"   Payload keys: {keys}")
    
    # Test count
    print(f"\n6. Testing count...")
    count = handler.count()
    print(f"   Total points: {count}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_qdrant_handler()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
