import json
import csv
from pathlib import Path
import tempfile

from script.denormalize import denormalize_csv


def test_denormalize_idempotent():
    """Test that running denormalization twice produces the same result (idempotency)"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_dir = tmpdir / "test_source"
        source_dir.mkdir()
        
        # Create the main CSV file
        main_csv = source_dir / "products.csv"
        main_data = [
            ["ProductID", "CategoryID", "ProductName"],
            ["1", "101", "Widget A"],
            ["2", "102", "Widget B"],
            ["3", "101", "Widget C"],
        ]
        with main_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(main_data)
        
        # Create the lookup CSV file
        lookup_csv = source_dir / "categories.csv"
        lookup_data = [
            ["CategoryID", "CategoryName", "CategoryDesc"],
            ["101", "Electronics", "Electronic devices"],
            ["102", "Furniture", "Home furniture"],
            ["103", "Books", "Reading materials"],
        ]
        with lookup_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lookup_data)
        
        # Create the meta.json file
        meta_file = source_dir / "products.csv.meta.json"
        meta_content = {
            "denormalized": [
                {
                    "column": "CategoryID",
                    "source": "test_source.xlsx",
                    "sheet": "categories.csv",
                    "key": "CategoryID",
                    "fields": ["CategoryName", "CategoryDesc"]
                }
            ]
        }
        with meta_file.open('w', encoding='utf-8') as f:
            json.dump(meta_content, f, indent=2)
        
        # Run denormalization the first time
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        # Read the result after first run
        with main_csv.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            result_first = list(reader)
        
        expected = [
            ["ProductID", "CategoryID", "ProductName", "CategoryName", "CategoryDesc"],
            ["1", "101", "Widget A", "Electronics", "Electronic devices"],
            ["2", "102", "Widget B", "Furniture", "Home furniture"],
            ["3", "101", "Widget C", "Electronics", "Electronic devices"],
        ]
        
        assert result_first == expected, f"First run - Expected {expected}, got {result_first}"
        
        # Run denormalization a SECOND time on the same file
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        # Read the result after second run
        with main_csv.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            result_second = list(reader)
        
        # Result should be identical (no duplicate columns)
        assert result_second == expected, f"Second run - Expected {expected}, got {result_second}"
        assert result_first == result_second, "Results should be identical after running twice"


def test_denormalize_update_values():
    """Test that running denormalization twice updates values if lookup data changes"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        source_dir = tmpdir / "test_source"
        source_dir.mkdir()
        
        # Create the main CSV file
        main_csv = source_dir / "products.csv"
        main_data = [
            ["ProductID", "CategoryID", "ProductName"],
            ["1", "101", "Widget A"],
        ]
        with main_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(main_data)
        
        # Create the lookup CSV file with initial data
        lookup_csv = source_dir / "categories.csv"
        lookup_data = [
            ["CategoryID", "CategoryName"],
            ["101", "Electronics"],
        ]
        with lookup_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lookup_data)
        
        # Create the meta.json file
        meta_file = source_dir / "products.csv.meta.json"
        meta_content = {
            "denormalized": [
                {
                    "column": "CategoryID",
                    "source": "test_source.xlsx",
                    "sheet": "categories.csv",
                    "key": "CategoryID",
                    "fields": ["CategoryName"]
                }
            ]
        }
        with meta_file.open('w', encoding='utf-8') as f:
            json.dump(meta_content, f, indent=2)
        
        # Run denormalization the first time
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        # Read the result
        with main_csv.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            result_first = list(reader)
        
        assert result_first == [
            ["ProductID", "CategoryID", "ProductName", "CategoryName"],
            ["1", "101", "Widget A", "Electronics"],
        ]
        
        # Update the lookup CSV with different data
        lookup_data_updated = [
            ["CategoryID", "CategoryName"],
            ["101", "Consumer Electronics"],  # Changed value
        ]
        with lookup_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lookup_data_updated)
        
        # Run denormalization again
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        # Read the result after second run
        with main_csv.open('r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            result_second = list(reader)
        
        # Values should be updated
        assert result_second == [
            ["ProductID", "CategoryID", "ProductName", "CategoryName"],
            ["1", "101", "Widget A", "Consumer Electronics"],  # Updated value
        ]
