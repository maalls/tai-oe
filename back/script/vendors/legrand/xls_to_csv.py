#!/usr/bin/env python3
"""
Convert legrand-tarif-professionnel-reference-ht.xlsx to CSV files.
Uses the xlsx_to_csv tool from src/
"""

from pathlib import Path

import sys

from src.xlsx_to_csv import xlsx_to_csv


def main():
    """Convert legrand spreadsheet to CSV."""
    config_path = Path("config.yml").resolve()
    # Check if config file exists
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return 1
    
    # Read legrand_filepath from config.yml
    import yaml
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    print("🔍 Reading configuration...")
    legrand_config = config.get("app", {})
    input_file_name = legrand_config.get("legrand_filepath", "var/storage/legrand-tarif-professionnel-reference-ht.xlsx")
    output_dir_name = legrand_config.get("legrand_csv_output_dir", "var/storage/legrand-tarif-professionnel-reference-ht")
    
    print(f"📁 Legrand input file: {input_file_name}")
    print(f"📁 CSV output directory: {output_dir_name}")
    
    input_file = Path(input_file_name)
    output_dir = Path(output_dir_name)
    
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        return 1
    
    print(f"📊 Converting {input_file.name} to CSV...")
    print(f"   Input: {input_file}")
    print(f"   Output: {output_dir}\n")
    
    try:
        xlsx_to_csv(input_file, output_dir)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
