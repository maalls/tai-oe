#!/usr/bin/env python3
from pathlib import Path
import sys
from script.googledrive.googledrive import GoogleDriveDownloader

from config import get_vendor_config
 
downloader = GoogleDriveDownloader()

sheet_url = "https://docs.google.com/spreadsheets/d/1cglDD_gkEMg7Cr5ELqI-v9w6FTphwvB5/edit?gid=979023516#gid=979023516"

# Resolve output path relative to back folder (where config.yml is)
back_dir = Path(__file__).parent.parent.parent.parent
config = get_vendor_config("yuasa")
output_path = back_dir / config.get("file_path")
output_path.parent.mkdir(parents=True, exist_ok=True)

print("📥 Downloading", sheet_url)
file_path = downloader.download(sheet_url, output_path=str(output_path))
print(f"   ✅ Saved to: {file_path}")