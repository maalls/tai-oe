#!/usr/bin/env python3
"""
Convert local XLSX file to multiple CSV files (one per sheet).

Usage:
  python3 script/xlsx_to_csv.py <INPUT_FILE> [OUTPUT_DIR]

Example:
  python3 script/xlsx_to_csv.py ./var/data/electric-parts-vendor/file.xlsx ./var/data/electric-parts-vendor
"""
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)


def xlsx_to_csv(input_file: Path, output_dir: Path) -> None:
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Reading {input_file.name}...")
    try:
        workbook = pd.ExcelFile(str(input_file))
        sheets = workbook.sheet_names
        print(f"Found {len(sheets)} sheet(s): {', '.join(sheets)}\n")
        for sheet in sheets:
            print(f"Converting: {sheet}")
            dataframe = pd.read_excel(str(input_file), sheet_name=sheet)
            safe_name = ''.join(char if char.isalnum() or char in '_-' else '_' for char in sheet)
            csv_path = output_dir / f"{safe_name}.csv"
            dataframe.to_csv(str(csv_path), index=False)
            print(f"  OK {csv_path.name} ({len(dataframe)} rows, {len(dataframe.columns)} cols)")
        print("\nConversion complete!")
        print(f"Files saved to: {output_dir}")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.parent
    xlsx_to_csv(input_file, output_dir)


if __name__ == '__main__':
    main()
