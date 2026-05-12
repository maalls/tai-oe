import pytest
import json
import csv
from pathlib import Path
import tempfile
import sys

from script.denormalize import denormalize_csv, process_storage_directory


# Helper functions to reduce duplication

def create_csv(path: Path, data: list):
    """Write CSV data to a file."""
    with path.open('w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(data)


def read_csv(path: Path) -> list:
    """Read CSV data from a file."""
    with path.open('r', newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def create_meta(path: Path, denormalized: list):
    """Write a meta.json file with denormalized config."""
    with path.open('w', encoding='utf-8') as f:
        json.dump({"denormalized": denormalized}, f, indent=2)


def setup_source_dir(tmpdir: Path) -> Path:
    """Create and return a source directory."""
    source_dir = tmpdir / "test_source"
    source_dir.mkdir()
    return source_dir



def test_denormalize_simple_case():
    """Test denormalization with a simple case: adding fields from a lookup table"""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "products.csv"
        create_csv(main_csv, [
            ["ProductID", "CategoryID", "ProductName"],
            ["1", "101", "Widget A"],
            ["2", "102", "Widget B"],
            ["3", "101", "Widget C"],
        ])
        
        create_csv(source_dir / "categories.csv", [
            ["CategoryID", "CategoryName", "CategoryDesc"],
            ["101", "Electronics", "Electronic devices"],
            ["102", "Furniture", "Home furniture"],
            ["103", "Books", "Reading materials"],
        ])
        
        meta_file = source_dir / "products.csv.meta.json"
        create_meta(meta_file, [{
            "column": "CategoryID",
            "source": "test_source.xlsx",
            "sheet": "categories.csv",
            "key": "CategoryID",
            "fields": ["CategoryName", "CategoryDesc"]
        }])
        
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["ProductID", "CategoryID", "ProductName", "CategoryName", "CategoryDesc"],
            ["1", "101", "Widget A", "Electronics", "Electronic devices"],
            ["2", "102", "Widget B", "Furniture", "Home furniture"],
            ["3", "101", "Widget C", "Electronics", "Electronic devices"],
        ]
        assert result == expected


def test_denormalize_missing_key():
    """Test denormalization when a key value is not found in the lookup table"""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "products.csv"
        create_csv(main_csv, [
            ["ProductID", "CategoryID", "ProductName"],
            ["1", "101", "Widget A"],
            ["2", "999", "Widget B"],  # 999 doesn't exist in categories
        ])
        
        create_csv(source_dir / "categories.csv", [
            ["CategoryID", "CategoryName"],
            ["101", "Electronics"],
        ])
        
        meta_file = source_dir / "products.csv.meta.json"
        create_meta(meta_file, [{
            "column": "CategoryID",
            "source": "test_source.xlsx",
            "sheet": "categories.csv",
            "key": "CategoryID",
            "fields": ["CategoryName"]
        }])
        
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["ProductID", "CategoryID", "ProductName", "CategoryName"],
            ["1", "101", "Widget A", "Electronics"],
            ["2", "999", "Widget B", "999"],  # Falls back to existing key value
        ]
        assert result == expected


def test_denormalize_missing_key_field_defaults_to_column():
    """If config omits key, use the column name as the lookup key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "features.csv"
        create_csv(main_csv, [
            ["FEATUREID", "FVALUE"],
            ["F1", "V1"],
            ["F2", "V2"],
        ])
        
        create_csv(source_dir / "values.csv", [
            ["FVALUE", "VALUEDESC"],
            ["V1", "Value One"],
            ["V2", "Value Two"],
        ])
        
        meta_file = source_dir / "features.csv.meta.json"
        create_meta(meta_file, [{
            "column": "FVALUE",
            "source": "test_source.xlsx",
            "sheet": "values.csv",
            "fields": ["VALUEDESC"],
        }])
        
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["FEATUREID", "FVALUE", "VALUEDESC"],
            ["F1", "V1", "Value One"],
            ["F2", "V2", "Value Two"],
        ]
        assert result == expected


def test_denormalize_raises_when_lookup_missing():
    """If the lookup CSV is missing, raise instead of silently skipping."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "features.csv"
        create_csv(main_csv, [
            ["FEATUREID", "FVALUE"],
            ["F1", "V1"],
        ])
        
        meta_file = source_dir / "features.csv.meta.json"
        create_meta(meta_file, [{
            "column": "FVALUE",
            "source": "test_source.xlsx",
            "sheet": "missing.csv",
            "fields": ["VALUEDESC"],
        }])
        
        with pytest.raises(ValueError):
            denormalize_csv(main_csv, meta_file, source_dir, source_dir)


def test_process_storage_directory_raises_on_missing_lookup():
    """process_storage_directory should fail-fast when lookup is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / "storage"
        storage_dir.mkdir()
        source_dir = storage_dir / "test_source"
        source_dir.mkdir()
        
        main_csv = source_dir / "features.csv"
        create_csv(main_csv, [
            ["FEATUREID", "FVALUE"],
            ["F1", "V1"],
        ])
        
        meta_file = source_dir / "features.csv.meta.json"
        create_meta(meta_file, [{
            "column": "FVALUE",
            "source": "test_source.xlsx",
            "sheet": "missing.csv",
            "fields": ["VALUEDESC"],
        }])
        
        with pytest.raises(ValueError):
            process_storage_directory(storage_dir)


def test_process_storage_directory_handles_meta_without_csv_suffix():
    """Meta named without `.csv` should still map to `<name>.csv`."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / "storage"
        storage_dir.mkdir()
        source_dir = storage_dir / "src"
        source_dir.mkdir()
        
        main_csv = source_dir / "orders.csv"
        create_csv(main_csv, [
            ["OrderID", "ProductID"],
            ["1", "P1"],
        ])
        
        create_csv(source_dir / "products.csv", [
            ["ProductID", "ProductName"],
            ["P1", "Widget"],
        ])
        
        meta_file = source_dir / "orders.meta.json"
        create_meta(meta_file, [{
            "column": "ProductID",
            "sheet": "products.csv",
            "fields": ["ProductName"],
        }])
        
        process_storage_directory(storage_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["OrderID", "ProductID", "ProductName"],
            ["1", "P1", "Widget"],
        ]
        assert result == expected


def test_denormalize_multiple_lookups():
    """Test denormalization with multiple lookup tables"""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "orders.csv"
        create_csv(main_csv, [
            ["OrderID", "ProductID", "CustomerID"],
            ["1", "P1", "C1"],
            ["2", "P2", "C2"],
        ])
        
        create_csv(source_dir / "products.csv", [
            ["ProductID", "ProductName"],
            ["P1", "Widget"],
            ["P2", "Gadget"],
        ])
        
        create_csv(source_dir / "customers.csv", [
            ["CustomerID", "CustomerName"],
            ["C1", "Alice"],
            ["C2", "Bob"],
        ])
        
        meta_file = source_dir / "orders.csv.meta.json"
        create_meta(meta_file, [
            {
                "column": "ProductID",
                "source": "test_source.xlsx",
                "sheet": "products.csv",
                "key": "ProductID",
                "fields": ["ProductName"]
            },
            {
                "column": "CustomerID",
                "source": "test_source.xlsx",
                "sheet": "customers.csv",
                "key": "CustomerID",
                "fields": ["CustomerName"]
            }
        ])
        
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["OrderID", "ProductID", "CustomerID", "ProductName", "CustomerName"],
            ["1", "P1", "C1", "Widget", "Alice"],
            ["2", "P2", "C2", "Gadget", "Bob"],
        ]
        assert result == expected


def test_denormalize_composite_key_lookup():
    """Support multi-column key lookups and fallback when missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = setup_source_dir(Path(tmpdir))
        
        main_csv = source_dir / "class_features.csv"
        create_csv(main_csv, [
            ["ARTCLASSID", "FEATUREID", "Other"],
            ["EC000001", "EF000001", "x"],
            ["EC000003", "EF000003", "y"],
            ["EC999999", "EF999999", "z"],  # Missing pair
        ])
        
        create_csv(source_dir / "map.csv", [
            ["ARTCLASSID", "FEATUREID", "UNITDESC"],
            ["EC000001", "EF000001", "Ampere"],
            ["EC000003", "EF000003", "Volt"],
        ])
        
        meta_file = source_dir / "class_features.csv.meta.json"
        create_meta(meta_file, [{
            "column": ["ARTCLASSID", "FEATUREID"],
            "sheet": "map.csv",
            "key": ["ARTCLASSID", "FEATUREID"],
            "fields": ["UNITDESC"],
        }])
        
        denormalize_csv(main_csv, meta_file, source_dir, source_dir)
        
        result = read_csv(main_csv)
        expected = [
            ["ARTCLASSID", "FEATUREID", "Other", "UNITDESC"],
            ["EC000001", "EF000001", "x", "Ampere"],
            ["EC000003", "EF000003", "y", "Volt"],
            ["EC999999", "EF999999", "z", "EC999999/EF999999"],  # Fallback to combined key
        ]
        assert result == expected
