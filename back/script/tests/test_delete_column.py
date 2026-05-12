import csv
import json
import tempfile
from pathlib import Path
import sys

from script.delete_column import delete_column_file


def read_csv(path: Path):
    with path.open('r', newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def test_delete_middle_column():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        storage = tmpdir / 'storage'
        source_dir = storage / 'sourceA'
        source_dir.mkdir(parents=True)

        csv_path = source_dir / 'sheet1.csv'
        rows = [
            ['A','B','C','D'],
            ['a1','b1','c1','d1'],
            ['a2','b2','c2','d2'],
        ]
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)

        # remove column index 2 ('C')
        delete_column_file(csv_path, 2)
        result = read_csv(csv_path)
        assert result == [
            ['A','B','D'],
            ['a1','b1','d1'],
            ['a2','b2','d2'],
        ]


def test_delete_first_column():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        storage = tmpdir / 'storage'
        source_dir = storage / 'sourceA'
        source_dir.mkdir(parents=True)

        csv_path = source_dir / 'sheet1.csv'
        rows = [
            ['A','B'],
            ['a1','b1'],
            ['a2','b2'],
        ]
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)

        delete_column_file(csv_path, 0)
        result = read_csv(csv_path)
        assert result == [
            ['B'],
            ['b1'],
            ['b2'],
        ]


def test_delete_out_of_range_no_change():
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        storage = tmpdir / 'storage'
        source_dir = storage / 'sourceA'
        source_dir.mkdir(parents=True)

        csv_path = source_dir / 'sheet1.csv'
        rows = [
            ['A','B'],
            ['a1','b1'],
        ]
        with csv_path.open('w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)

        # index 5 is out of range, file should remain unchanged
        delete_column_file(csv_path, 5)
        result = read_csv(csv_path)
        assert result == rows
