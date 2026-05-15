#!/usr/bin/env python3
"""
Convert CSV files to JSON with headers as field names.

Usage:
  python3 script/csv_to_json.py <CSV_FILE_OR_DIR> [OUTPUT_DIR]

Examples:
  python3 script/csv_to_json.py ./var/data/electric-parts-vendor/B01_COMMERCE.csv ./var/data/json
  python3 script/csv_to_json.py ./var/data/electric-parts-vendor ./var/data/json
"""
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)


def csv_to_json(input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

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
            dataframe = pd.read_csv(csv_file)
            if dataframe.empty:
                print("  File is empty, skipping")
                continue

            records = dataframe.to_dict(orient='records')
            json_path = output_dir / f"{csv_file.stem}.json"
            json_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"  OK {json_path.name} ({len(records)} records)")
        except Exception as exc:
            print(f"  Error: {exc}")

    print("\nConversion complete!")
    print(f"Files saved to: {output_dir}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path.parent / 'json'
    csv_to_json(input_path, output_dir)


if __name__ == '__main__':
    main()
