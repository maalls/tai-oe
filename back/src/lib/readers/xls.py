import sys
from pathlib import Path
import pandas as pd

class XlsReader:

    def convertToCsv(input_file: Path, output_dir: Path):
    
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
            raise e