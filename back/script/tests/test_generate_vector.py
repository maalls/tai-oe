#!/usr/bin/env python3
"""Tests for generate_vector.py script."""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from script.generate_vector import generate_numeric_id, generaxte_vectors_from_commerce, get_products, get_product, serialize_value
from src.controller.db_client import DatabaseHandler

def test_get_products(db):
    rows = get_products(db, 5)
    assert len(rows) == 5, "Should fetch 5 rows from fabdis_commerce but got "  + str(len(rows))
    print("✓ test_get_products passed")

def test_get_product(db):

    payload = get_product({'marque': "MODELEC", 'libelle240': "Libelle240 content", 'refciale': "072001G"}, db)
    assert payload is not None, "Should fetch a product payload"
    print("✓ test_get_product passed")
    print('playload:', payload)
def test_generate_numeric_id():
    """Test that generate_numeric_id produces consistent numeric IDs."""
    # Same input should always produce same output
    id1 = generate_numeric_id("TEST123")
    id2 = generate_numeric_id("TEST123")
    assert id1 == id2, "Same input should produce same ID"
    
    # Different inputs should produce different outputs
    id3 = generate_numeric_id("TEST456")
    assert id1 != id3, "Different inputs should produce different IDs"
    
    # ID should be a positive integer
    assert isinstance(id1, int), "ID should be an integer"
    assert id1 > 0, "ID should be positive"
    
    print("✓ test_generate_numeric_id passed")

def test_generaxte_vectors_from_commerce():

    generaxte_vectors_from_commerce(
        collection_name="test_commerce_vectors", 
        limit=5, 
        batch_size=2,
        qdrant_path='http://localhost:6333'  # Assuming local RAG server
    )

    assert True, "Vector generation completed without errors"
    
def test_serialize_value():
    """Test that serialize_value handles different data types correctly."""
    # Test date serialization
    test_date = date(2026, 1, 15)
    assert serialize_value(test_date) == "2026-01-15"
    
    # Test datetime serialization
    test_datetime = datetime(2026, 1, 15, 10, 30, 45)
    assert serialize_value(test_datetime).startswith("2026-01-15")
    
    # Test Decimal serialization
    test_decimal = Decimal("123.45")
    assert serialize_value(test_decimal) == 123.45
    assert isinstance(serialize_value(test_decimal), float)
    
    # Test None
    assert serialize_value(None) is None
    
    # Test regular values pass through
    assert serialize_value("test") == "test"
    assert serialize_value(42) == 42
    
    print("✓ test_serialize_value passed")


if __name__ == "__main__":
    try:
        
        db = DatabaseHandler()
        test_get_products(db)
        test_get_product(db)
        test_generaxte_vectors_from_commerce()
        test_generate_numeric_id()
        test_serialize_value()
        print("\nAll tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
