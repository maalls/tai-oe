#!/usr/bin/env python3
"""
Export all sheets from a Google Spreadsheet to CSV files.

Usage:
  python -m src.google_drive.export_sheets_to_csv <SPREADSHEET_ID> [OUTPUT_DIR]
  
Example:
  python -m src.google_drive.export_sheets_to_csv 1YLJu91d9-yRMhHkqeCKCPOteqSrpQ7k0 ./csv_exports
"""
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

import argparse
import csv
import sys
from pathlib import Path

# Suppress importlib.metadata error messages
import io
import contextlib

_stderr_suppress = contextlib.redirect_stderr(io.StringIO())
_stderr_suppress.__enter__()

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

_stderr_suppress.__exit__(None, None, None)

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "var" / "gdrive"
CREDENTIALS_PATH = STORE / "credentials.json"
TOKEN_PATH = STORE / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials() -> Credentials:
    """Get Google credentials with OAuth flow."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Missing credentials: {CREDENTIALS_PATH}\n"
                    "Run: python3 scripts/gdrive_tool.py init"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def sanitize_filename(name: str) -> str:
    """Convert sheet name to valid filename."""
    # Replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()


def export_sheets_to_csv(spreadsheet_id: str, output_dir: Path):
    """Export all sheets from a spreadsheet to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    # Get spreadsheet metadata to find all sheets
    print(f"Fetching spreadsheet metadata...")
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    if not sheets:
        print("No sheets found in spreadsheet.")
        return
    
    print(f"Found {len(sheets)} sheet(s)")
    
    for sheet in sheets:
        sheet_title = sheet['properties']['title']
        print(f"\nExporting: {sheet_title}")
        
        # Read all data from this sheet
        range_name = f"'{sheet_title}'!A1:ZZ"  # Read up to column ZZ
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print(f"  ⚠ Sheet '{sheet_title}' is empty, skipping")
            continue
        
        # Write to CSV
        safe_name = sanitize_filename(sheet_title)
        csv_path = output_dir / f"{safe_name}.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for row in values:
                writer.writerow(row)
        
        print(f"  ✓ Saved to: {csv_path} ({len(values)} rows)")
    
    print(f"\n✓ Export complete! Files saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Export all sheets from a Google Spreadsheet to CSV files"
    )
    parser.add_argument(
        'spreadsheet_id',
        help='Google Spreadsheet ID (from the URL)'
    )
    parser.add_argument(
        'output_dir',
        nargs='?',
        default='./csv_exports',
        help='Output directory for CSV files (default: ./csv_exports)'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    try:
        export_sheets_to_csv(args.spreadsheet_id, output_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
