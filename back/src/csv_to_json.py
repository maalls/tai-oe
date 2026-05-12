#!/usr/bin/env python3
"""
Convert CSV files to JSON with headers as field names.

Usage:
  python3 scripts/csv_to_json.py <CSV_FILE_OR_DIR> [OUTPUT_DIR]

Examples:
  python3 scripts/csv_to_json.py ./var/data/electric-parts-vendor/B01_COMMERCE.csv ./var/data/json
  python3 scripts/csv_to_json.py ./var/data/electric-parts-vendor ./var/data/json
"""
import sys
import json
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)


def csv_to_json(input_path: Path, output_dir: Path):
    """Convert CSV file(s) to JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_files = []
    if input_path.is_file() and input_path.suffix == '.csv':
        csv_files = [input_path]
    elif input_path.is_dir():
        csv_files = sorted(input_path.glob('*.csv'))
    else:
        print(f"Error: {input_path} is not a CSV file or directory")
        sys.exit(1)
    
    if not csv_files:
        print(f"No CSV files found in {input_path}")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV file(s)\n")
    
    for csv_file in csv_files:
        print(f"Converting: {csv_file.name}")
        
        try:
            # Read CSV with headers
            df = pd.read_csv(csv_file)
            
            if df.empty:
                print(f"  ⚠ File is empty, skipping")
                continue
            
            # Convert to list of dicts (each row becomes a dict with headers as keys)
            records = df.to_dict(orient='records')
            
            # Create JSON file
            json_name = csv_file.stem + '.json'
            json_path = output_dir / json_name
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            print(f"  ✓ {json_path.name} ({len(records)} records)")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Conversion complete!")
    print(f"✓ Files saved to: {output_dir}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.parent / 'json'
    
    csv_to_json(input_path, output_dir)


if __name__ == '__main__':
    main()
