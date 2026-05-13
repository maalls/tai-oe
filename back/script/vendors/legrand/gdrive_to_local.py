#!/usr/bin/env python3
"""
Download Legrand tariff spreadsheet from Google Drive to var/storage.
Google Drive URL: https://docs.google.com/spreadsheets/d/1RuAczIm0l5875bkv_AIRsYRnJP4B2CIU
"""

from pathlib import Path
import sys

from script.vendors.googledrive.googledrive import GoogleDriveDownloader


def main():
    """Download Legrand spreadsheet from Google Drive."""
    # Google Sheet URL
    sheet_url = "https://docs.google.com/spreadsheets/d/1RuAczIm0l5875bkv_AIRsYRnJP4B2CIU/edit?gid=1089379931#gid=1089379931"
    
    # Output path
    output_path = "var/storage/legrand-tarif-professionnel-reference-ht.xlsx"
    
    print("🚀 Initializing Google Drive downloader...")
    downloader = GoogleDriveDownloader()
    
    print(f"\n📄 Google Sheet URL: {sheet_url}")
    print(f"📁 Output path: {output_path}\n")
    
    try:
        print("📥 Downloading...")
        file_path = downloader.download(sheet_url, output_path=output_path)
        print(f"   ✅ Saved to: {file_path}")
        print(f"   📊 Size: {file_path.stat().st_size / 1024:.1f} KB")
        print("\n✨ Download complete!")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())