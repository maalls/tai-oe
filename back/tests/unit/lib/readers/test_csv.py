import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

from src.lib.readers.csv import CSVReader


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("name,age,city\nAlice,30,New York\nBob,25,Los Angeles\nCharlie,35,Chicago\n")
    return csv_file


@pytest.fixture
def sample_semicolon_csv_file(tmp_path: Path) -> Path:
    """Create a sample semicolon-delimited CSV file"""
    csv_file = tmp_path / "sample_semi.csv"
    csv_file.write_text("name;age;city\nAlice;30;New York\nBob;25;Los Angeles\n")
    return csv_file


def test_csv_reader_reads_comma_delimited_file(sample_csv_file: Path):
    """Test that CSVReader can read comma-delimited CSV files"""
    reader = CSVReader()
    result = reader.read(sample_csv_file)
    
    assert isinstance(result, dict)
    assert "headers" in result
    assert "rows" in result
    assert "column_metadata" in result
    assert "total" in result
    assert result["headers"] == ["name", "age", "city"]
    assert len(result["rows"]) == 3
    assert result["total"] == 3
    assert result["rows"][0] == ["Alice", "30", "New York"]
    assert result["rows"][1][1] == "25"
    
    # Verify metadata structure
    assert isinstance(result["column_metadata"], list)
    assert len(result["column_metadata"]) == 3


def test_csv_reader_reads_semicolon_delimited_file(sample_semicolon_csv_file: Path):
    """Test that CSVReader can auto-detect semicolon delimiter"""
    reader = CSVReader()
    result = reader.read(sample_semicolon_csv_file)
    
    assert isinstance(result, dict)
    assert "column_metadata" in result
    assert "total" in result
    assert result["headers"] == ["name", "age", "city"]
    assert len(result["rows"]) == 2
    assert result["total"] == 2
    assert result["rows"][0] == ["Alice", "30", "New York"]
    assert result["rows"][1][1] == "25"


def test_csv_reader_returns_dict_with_headers_and_rows(sample_csv_file: Path):
    """Test that CSVReader returns dict with headers and rows"""
    reader = CSVReader()
    result = reader.read(sample_csv_file)
    
    assert isinstance(result, dict)
    assert isinstance(result["headers"], list)
    assert isinstance(result["rows"], list)
    assert isinstance(result["column_metadata"], list)
    assert isinstance(result["total"], int)
    assert all(isinstance(row, list) for row in result["rows"])


def test_csv_reader_supports_offset_and_limit(sample_csv_file: Path):
    """Test that CSVReader applies offset/limit and returns total rows"""
    reader = CSVReader()
    result = reader.read(sample_csv_file, offset=1, limit=1)

    assert result["headers"] == ["name", "age", "city"]
    assert result["total"] == 3
    assert len(result["rows"]) == 1
    assert result["rows"][0] == ["Bob", "25", "Los Angeles"]


def test_get_reversed_relations_builds_inbound_mapping():
    relations = {
        "A.csv": {
            "fk_to_b": {"sheet": "B.csv", "key": "id"},
            "fk_to_c": {"sheet": "C.csv", "key": "cid"},
        },
        "B.csv": {
            "fk_to_c2": {"sheet": "C.csv", "key": "cid"},
        },
    }

    reader = CSVReader()
    reversed_rel = reader.get_reversed_relations(relations)

    assert reversed_rel == {
        "B.csv": [
            {"source_file": "A.csv", "source_field": "fk_to_b", "key": "id"},
        ],
        "C.csv": [
            {"source_file": "A.csv", "source_field": "fk_to_c", "key": "cid"},
            {"source_file": "B.csv", "source_field": "fk_to_c2", "key": "cid"},
        ],
    }
