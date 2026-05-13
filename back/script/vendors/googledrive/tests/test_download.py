#!/usr/bin/env python3
"""
Test Google Drive downloader with a Google Sheets URL.
"""

import sys
from pathlib import Path

from script.vendors.googledrive.googledrive import GoogleDriveDownloader

def main():
    # Your Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/1cglDD_gkEMg7Cr5ELqI-v9w6FTphwvB5/edit?gid=979023516#gid=979023516"

    print("🚀 Initializing Google Drive downloader...")
    downloader = GoogleDriveDownloader()

    print(f"\n📄 Extracting file ID from URL...")
    file_id = downloader.extract_file_id(sheet_url)
    print(f"   File ID: {file_id}")

    file_type = downloader.get_file_type(file_id)
    print(f"   File type: {file_type}")

    # Create downloads directory
    downloads_dir = Path("var/downloads")
    downloads_dir.mkdir(exist_ok=True)

    try:
        # Download as XLSX (original format)
        print("\n📥 Downloading as XLSX (original format)...")
        xlsx_path = downloader.download(sheet_url, output_path="var/downloads/sheet.xlsx")
        print(f"   ✅ Saved to: {xlsx_path}")
        print(f"   📊 Size: {xlsx_path.stat().st_size / 1024:.1f} KB")

        print("\n✨ Done! File saved in var/downloads/")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
