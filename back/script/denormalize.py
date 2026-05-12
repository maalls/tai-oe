#!/usr/bin/env python3
"""
Denormalize CSV files based on meta.json configuration.

This script scans var/storage for *.meta.json files and denormalizes CSVs
by adding fields from lookup tables based on key columns.
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import chardet

from src.reader.csv import CSVReader


def _detect_encoding(path: Path) -> str:
    """Detect file encoding using a small byte sample."""
    try:
        with path.open('rb') as f:
            sample = f.read(32 * 1024)
        enc = chardet.detect(sample).get('encoding') or 'utf-8'
        return enc
    except Exception:
        return 'utf-8'


def _detect_delimiter(path: Path, encoding: str) -> str:
    """Detect CSV delimiter using csv.Sniffer; fall back to comma."""
    try:
        with path.open('r', encoding=encoding, errors='replace') as f:
            sample = f.read(8192)
        sniffer = csv.Sniffer()
        return sniffer.sniff(sample, delimiters=',;\t|').delimiter
    except Exception:
        return ','


def denormalize_csv(csv_file: Path, meta_file: Path, source_dir: Path, storage_root: Path) -> None:
    """
    Denormalize a CSV file based on its meta.json configuration.
    
    Args:
        csv_file: Path to the CSV file to denormalize
        meta_file: Path to the meta.json file
        source_dir: Directory containing the current CSV (for same-source lookups)
        storage_root: Root storage directory (for cross-source lookups)
    """
    # Read the meta configuration
    with meta_file.open('r', encoding='utf-8') as f:
        meta = json.load(f)
    denorm_configs = meta.get('denormalized', [])
    if not denorm_configs:
        return
    
    # Read the main CSV via CSVReader
    csv_reader = CSVReader()
    main_payload = csv_reader.read(csv_file, offset=0, limit=None)
    headers = main_payload.get('headers', [])
    rows = main_payload.get('rows', [])
    main_encoding = (main_payload.get('encoding') or 'utf-8')
    if not main_encoding or main_encoding.lower() == 'ascii':
        main_encoding = 'utf-8'
    main_delimiter = (main_payload.get('delimiter') or ',')
    
    # Process each denormalization configuration
    for config in denorm_configs:
        column = config['column']
        lookup_source = config.get('source', '')  # e.g., "ETIM.xlsx"
        lookup_sheet = config['sheet']
        # Normalize column and key to lists to support composite keys
        column_list = column if isinstance(column, list) else [column]
        raw_key = config.get('key', column_list) or column_list
        lookup_key_list = raw_key if isinstance(raw_key, list) else [raw_key]
        fields = config['fields']
        
        # Find the lookup CSV file - try multiple locations
        lookup_file = None
        
        # First try: same directory
        candidate = source_dir / lookup_sheet
        if candidate.exists():
            lookup_file = candidate
        
        # Second try: cross-source lookup based on source name
        if not lookup_file and lookup_source:
            # Strip extension from source to get directory name
            source_name = lookup_source.rsplit('.', 1)[0]
            candidate = storage_root / source_name / lookup_sheet
            if candidate.exists():
                lookup_file = candidate
        
        # Third try: search all subdirectories in storage root
        if not lookup_file:
            for candidate in storage_root.rglob(lookup_sheet):
                if candidate.is_file():
                    lookup_file = candidate
                    break
        
        if not lookup_file:
            raise ValueError(
                f"Lookup file {lookup_sheet} not found (tried same-source and cross-source)"
            )
        
        # Build lookup dictionary from the lookup CSV
        lookup_dict = {}
        # Read lookup CSV via CSVReader
        lookup_payload = csv_reader.read(lookup_file, offset=0, limit=None)
        lookup_headers = lookup_payload.get('headers', [])
        lookup_rows = lookup_payload.get('rows', [])

        # Find indices for the key (support composite keys) and fields
        key_indices: List[int] = []
        try:
            for k in lookup_key_list:
                key_indices.append(lookup_headers.index(k))
        except ValueError:
            print(f"Warning: Key column(s) {lookup_key_list} not found in {lookup_sheet}, skipping")
            continue

        field_indices = []
        for field in fields:
            try:
                field_indices.append(lookup_headers.index(field))
            except ValueError:
                print(f"Warning: Field {field} not found in {lookup_sheet}, skipping")
                continue

        # Build the lookup dictionary
        for row in lookup_rows:
            # Build composite key tuple from key_indices
            key_parts = []
            for ki in key_indices:
                key_parts.append(row[ki] if ki < len(row) else '')
            key_value = tuple(key_parts)
            field_values = [row[idx] if idx < len(row) else '' for idx in field_indices]
            lookup_dict[key_value] = field_values
        
        # Find the column index in the main CSV
        # Find column indices in the main CSV (support composite keys)
        col_indices: List[int] = []
        try:
            for c in column_list:
                col_indices.append(headers.index(c))
        except ValueError:
            print(f"Warning: Column(s) {column_list} not found in {csv_file.name}, skipping")
            continue
        
        # Check if fields already exist (for idempotency - running script multiple times)
        field_indices_to_update = []
        fields_to_add = []
        
        for field in fields:
            if field in headers:
                # Field already exists, we'll update it in place
                field_indices_to_update.append(headers.index(field))
                fields_to_add.append(None)  # Placeholder
            else:
                # New field, add to headers
                field_indices_to_update.append(len(headers))
                headers.append(field)
                fields_to_add.append(field)
        
        # Denormalize each row
        for row in rows:
            # Extend row if it's shorter than headers (for new columns)
            while len(row) < len(headers):
                row.append('')

            # Build composite key from the row values
            key_parts = []
            for ci in col_indices:
                key_parts.append(row[ci] if ci < len(row) else '')
            key_value = tuple(key_parts)

            # If no lookup hit, fall back to the combined existing value
            fallback_str = "/".join(key_parts)
            fallback_values = [fallback_str] * len(fields)
            field_values = lookup_dict.get(key_value, fallback_values)

            # Update or set the denormalized values
            for i, val in enumerate(field_values):
                row[field_indices_to_update[i]] = val

    # Write the denormalized CSV back to the same file (preserve encoding & delimiter)
    with csv_file.open('w', newline='', encoding=main_encoding) as f:
        writer = csv.writer(f, delimiter=main_delimiter)
        writer.writerow(headers)
        writer.writerows(rows)
    
def process_storage_directory(storage_dir: Path) -> None:
    """
    Process all meta.json files in the storage directory and denormalize CSVs.
    
    Args:
        storage_dir: Path to var/storage directory
    """
    if not storage_dir.exists():
        print(f"Error: Storage directory {storage_dir} does not exist")
        return
    
    # Find all meta.json files
    meta_files = list(storage_dir.rglob('*.meta.json'))
    
    print(f"Found {len(meta_files)} meta.json files")
    
    for meta_file in meta_files:
        # Determine the corresponding CSV file
        csv_file_name = meta_file.name.replace('.meta.json', '')
        csv_file = meta_file.parent / csv_file_name
        # Fallback: if meta is named without .csv in the basename, try adding .csv
        if not csv_file.exists():
            csv_with_ext = meta_file.parent / f"{csv_file_name}.csv"
            if csv_with_ext.exists():
                csv_file = csv_with_ext
            else:
                print(f"Warning: CSV file {csv_file} not found for {meta_file}, skipping")
                continue
        
        print(f"Processing {csv_file.name}...")
        
        # Fail fast: propagate errors to stop the run and signal non-zero exit
        denormalize_csv(csv_file, meta_file, meta_file.parent, storage_dir)
        print(f"✓ Denormalized {csv_file.name}")


def main():
    """Main entry point for the script."""
    # Determine storage directory
    if len(sys.argv) > 1:
        storage_dir = Path(sys.argv[1])
    else:
        # Default to var/storage relative to this script
        script_dir = Path(__file__).parent
        storage_dir = script_dir.parent / 'var' / 'storage'
    
    print(f"Processing storage directory: {storage_dir}")
    process_storage_directory(storage_dir)


if __name__ == '__main__':
    main()
