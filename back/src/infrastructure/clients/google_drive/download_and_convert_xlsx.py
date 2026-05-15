#!/usr/bin/env python3
"""
Download XLS/XLSX file from Google Drive and convert to CSV.

Usage:
    python -m src.infrastructure.clients.google_drive.download_and_convert_xlsx <FILE_ID> [OUTPUT_DIR]

Example:
    python -m src.infrastructure.clients.google_drive.download_and_convert_xlsx 1abc2def3ghi ./var/data/electric-parts-vendor
"""
import sys
from pathlib import Path

# Try importing required libraries
try:
    import pandas as pd
except ImportError:
    print("Error: pandas not installed")
    print("Install with: pip install pandas openpyxl")
    sys.exit(1)

import requests


def download_and_convert(file_id: str, output_dir: Path):
    """Download XLSX from Google Drive and convert all sheets to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Google Drive direct download URL
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    print(f"Downloading file {file_id}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error downloading: {e}")
        sys.exit(1)
    
    # Save to temp file
    temp_file = output_dir / "temp.xlsx"
    temp_file.write_bytes(response.content)
    print(f"✓ Downloaded {temp_file.stat().st_size / 1024:.1f} KB")
    
    # Read Excel file and convert each sheet to CSV
    try:
        xls = pd.ExcelFile(str(temp_file))
        sheets = xls.sheet_names
        print(f"Found {len(sheets)} sheet(s): {', '.join(sheets)}")
        
        for sheet in sheets:
            print(f"\nConverting: {sheet}")
            df = pd.read_excel(str(temp_file), sheet_name=sheet)
            
            # Sanitize sheet name for filename
            safe_name = "".join(c if c.isalnum() or c in '_-' else '_' for c in sheet)
            csv_path = output_dir / f"{safe_name}.csv"
            
            df.to_csv(str(csv_path), index=False)
            print(f"  ✓ Saved: {csv_path} ({len(df)} rows)")
        
        # Cleanup
        temp_file.unlink()
        print(f"\n✓ Conversion complete! Files saved to: {output_dir}")
    
    except Exception as e:
        print(f"Error converting: {e}")
        temp_file.unlink()
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    file_id = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('./csv_exports')
    
    download_and_convert(file_id, output_dir)


if __name__ == '__main__':
    main()
