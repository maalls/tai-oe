#!/usr/bin/env python3
"""
Delete a column from a CSV under var/storage given source + sheet and index.

Usage:
  python back/script/delete_column.py --storage back/var/storage --source "ETIM.xlsx" --sheet "ETIMARTCLASS.csv" --index 3
  python back/script/delete_column.py --path /abs/path/to/file.csv --index 1

If --source is provided, the CSV is resolved under <storage>/<source-without-ext>/<sheet>.
If --path is provided, it is used directly.
Writes changes back to the same CSV file.
"""

import argparse
import csv
from pathlib import Path
from typing import Optional


def delete_column_file(csv_file: Path, index: int) -> None:
    """Delete a column at index (0-based) from a CSV file, saving in place."""
    if index < 0:
        print(f"Warning: index {index} is negative; skipping")
        return

    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        return

    # Read
    with csv_file.open('r', newline='', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    if not reader:
        print(f"Warning: CSV file is empty: {csv_file}")
        return

    # Validate width
    width = len(reader[0])
    if index >= width:
        print(f"Warning: index {index} out of range (columns={width}) for {csv_file}; skipping")
        return

    # Remove index from each row
    new_rows = []
    for row in reader:
        # Guard against ragged rows
        if index < len(row):
            new_row = row[:index] + row[index+1:]
        else:
            new_row = row
        new_rows.append(new_row)

    # Write back
    with csv_file.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)
    print(f"✓ Removed column {index} from {csv_file}")


def resolve_csv_path(storage: Path, source: Optional[str], sheet: Optional[str], path: Optional[str]) -> Optional[Path]:
    if path:
        return Path(path)
    if source and sheet:
        source_dir = storage / source.rsplit('.', 1)[0]
        return source_dir / sheet
    return None


def main():
    parser = argparse.ArgumentParser(description="Delete a column from a CSV by index")
    parser.add_argument('--storage', type=str, default=str(Path(__file__).parent.parent / 'var' / 'storage'))
    parser.add_argument('--source', type=str, help='Source file name (e.g., ETIM.xlsx)')
    parser.add_argument('--sheet', type=str, help='Sheet CSV name (e.g., ETIMARTCLASS.csv)')
    parser.add_argument('--path', type=str, help='Direct path to CSV file')
    parser.add_argument('--index', type=int, required=True, help='0-based column index to remove')

    args = parser.parse_args()

    storage = Path(args.storage)
    csv_path = resolve_csv_path(storage, args.source, args.sheet, args.path)
    if not csv_path:
        print('Error: provide either --path or both --source and --sheet')
        return

    delete_column_file(csv_path, args.index)


if __name__ == '__main__':
    main()
