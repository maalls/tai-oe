#!/usr/bin/env python3
"""
Convert local XLSX file to multiple CSV files (one per sheet).

Usage:
  python3 scripts/xlsx_to_csv.py <INPUT_FILE> [OUTPUT_DIR]

Example:
  python3 scripts/xlsx_to_csv.py ./var/data/electric-parts-vendor/file.xlsx ./var/data/electric-parts-vendor
"""
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)


def xlsx_to_csv(input_file: Path, output_dir: Path):
    """Convert all sheets in XLSX to separate CSV files."""
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Reading {input_file.name}...")
    try:
        xls = pd.ExcelFile(str(input_file))
        sheets = xls.sheet_names
        print(f"Found {len(sheets)} sheet(s): {', '.join(sheets)}\n")
        
        for sheet in sheets:
            print(f"Converting: {sheet}")
            df = pd.read_excel(str(input_file), sheet_name=sheet)
            
            # Sanitize sheet name for filename
            safe_name = "".join(c if c.isalnum() or c in '_-' else '_' for c in sheet)
            csv_path = output_dir / f"{safe_name}.csv"
            
            df.to_csv(str(csv_path), index=False)
            print(f"  ✓ {csv_path.name} ({len(df)} rows, {len(df.columns)} cols)")
        
        print(f"\n✓ Conversion complete!")
        print(f"✓ Files saved to: {output_dir}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.parent
    
    xlsx_to_csv(input_file, output_dir)


if __name__ == '__main__':
    main()
