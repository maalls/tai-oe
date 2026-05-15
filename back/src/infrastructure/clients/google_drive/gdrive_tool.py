#!/usr/bin/env python3
"""
Google Drive Management CLI
- Auth (OAuth installed app) and token caching
- Drive: list folder, upload, download
- Sheets: read range, append rows
- Docs: read text, append text

Credentials:
- Place OAuth client JSON at var/gdrive/credentials.json
- First run "init" to create var/gdrive/token.json

Usage examples:
    python -m src.infrastructure.clients.google_drive.gdrive_tool init
    python -m src.infrastructure.clients.google_drive.gdrive_tool drive list --folder-id <FOLDER_ID>
    python -m src.infrastructure.clients.google_drive.gdrive_tool drive upload --folder-id <FOLDER_ID> --path ./file.txt --mime text/plain
    python -m src.infrastructure.clients.google_drive.gdrive_tool sheets read --sheet-id <SPREADSHEET_ID> --range "Sheet1!A1:C10"
    python -m src.infrastructure.clients.google_drive.gdrive_tool sheets append --sheet-id <SPREADSHEET_ID> --range "Sheet1!A1" --values "a,b,c"
    python -m src.infrastructure.clients.google_drive.gdrive_tool docs read --doc-id <DOCUMENT_ID>
    python -m src.infrastructure.clients.google_drive.gdrive_tool docs append --doc-id <DOCUMENT_ID> --text "Hello world"
"""
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

import argparse
import os
import sys
from pathlib import Path
from typing import List

# Require Python 3 when invoked via 'python'
if sys.version_info.major < 3:
    sys.stderr.write("This tool requires Python 3. Please run with 'python3' or execute the script directly.\n")
    sys.exit(1)

# Suppress importlib.metadata error messages
import io
import contextlib

_stderr_suppress = contextlib.redirect_stderr(io.StringIO())
_stderr_suppress.__enter__()

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

_stderr_suppress.__exit__(None, None, None)
import io

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "var" / "gdrive"
STORE.mkdir(parents=True, exist_ok=True)
CREDENTIALS_PATH = STORE / "credentials.json"
TOKEN_PATH = STORE / "token.json"

# Scopes: Sheets and Drive full access
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_credentials() -> Credentials:
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
                    "Create OAuth Desktop app credentials in Google Cloud Console:\n"
                    "  APIs & Services → Credentials → Create credentials → OAuth client ID → Desktop app\n"
                    "  Download the JSON and save to var/gdrive/credentials.json"
                )
            # Validate credential type before attempting OAuth flow
            import json as json_mod
            try:
                with open(CREDENTIALS_PATH) as f:
                    cred_data = json_mod.load(f)
                if "installed" not in cred_data and "web" not in cred_data:
                    raise ValueError(
                        f"Invalid credentials.json: must be OAuth client (Desktop or Web app), not service account.\n"
                        f"Go to Google Cloud Console:\n"
                        f"  APIs & Services → Credentials → Create credentials → OAuth client ID → Desktop app\n"
                        f"  Download the JSON and replace {CREDENTIALS_PATH}"
                    )
            except (json_mod.JSONDecodeError, KeyError, FileNotFoundError) as e:
                raise ValueError(f"Cannot parse credentials.json: {e}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def svc_drive(creds=None):
    if creds is None:
        creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def svc_sheets(creds=None):
    if creds is None:
        creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


def svc_docs(creds=None):
    if creds is None:
        creds = get_credentials()
    return build("docs", "v1", credentials=creds)


# ------- Drive operations -------

def drive_list(folder_id: str):
    from datetime import datetime
    service = svc_drive()
    q = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=q, 
        fields="files(id, name, mimeType, owners, modifiedTime, size)",
        orderBy="folder,name"
    ).execute()
    files = results.get("files", [])
    
    if not files:
        print("(empty)")
        return
    
    # Format like ls -lh: type, size, date, name
    for f in files:
        # Type indicator (d for folder, - for file)
        is_folder = f['mimeType'] == 'application/vnd.google-apps.folder'
        type_char = 'd' if is_folder else '-'
        
        # Size (folders show '-', files show human-readable size)
        size_str = '-' if is_folder else format_size(f.get('size', '0'))
        
        # Modified date (like ls: Dec 27 14:30)
        mod_time = datetime.fromisoformat(f['modifiedTime'].replace('Z', '+00:00'))
        date_str = mod_time.strftime('%b %d %H:%M')
        
        # Name (append / to folders for clarity)
        name = f['name'] + ('/' if is_folder else '')
        
        print(f"{type_char}  {size_str:>8}  {date_str}  {name}")


def format_size(size_bytes):
    """Convert bytes to human-readable format (K, M, G)."""
    try:
        size = int(size_bytes)
    except (ValueError, TypeError):
        return '0'
    
    if size == 0:
        return '0'
    
    units = ['', 'K', 'M', 'G', 'T']
    unit_idx = 0
    size_float = float(size)
    
    while size_float >= 1024 and unit_idx < len(units) - 1:
        size_float /= 1024
        unit_idx += 1
    
    if unit_idx == 0:
        return f"{int(size_float)}"
    else:
        return f"{size_float:.1f}{units[unit_idx]}"


def drive_upload(folder_id: str, path: str, mime: str = None):
    service = svc_drive()
    file_name = os.path.basename(path)
    media = MediaFileUpload(path, mimetype=mime, resumable=True)
    file_metadata = {"name": file_name, "parents": [folder_id]}
    file = service.files().create(body=file_metadata, media_body=media, fields="id,name").execute()
    print(f"Uploaded: {file['name']} ({file['id']})")


def drive_download(file_id: str, dest: str):
    service = svc_drive()
    dest_path = Path(dest)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(str(dest_path), 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    print(f"Downloaded to {dest_path}")


# ------- Sheets operations -------

def sheets_read(sheet_id: str, range_a1: str):
    service = svc_sheets()
    resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_a1).execute()
    values = resp.get("values", [])
    for row in values:
        print(",".join(str(v) for v in row))


def sheets_append(sheet_id: str, range_a1: str, csv_values: str):
    service = svc_sheets()
    values: List[List[str]] = [list(v.strip() for v in csv_values.split(","))]
    body = {"values": values}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_a1,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print("Appended row.")


# ------- Docs operations -------

def docs_read(doc_id: str):
    service = svc_docs()
    resp = service.documents().get(documentId=doc_id).execute()
    # Flatten text from the document structure
    text_chunks: List[str] = []
    for c in resp.get("body", {}).get("content", []):
        p = c.get("paragraph")
        if not p:
            continue
        for el in p.get("elements", []):
            ts = el.get("textRun", {}).get("content")
            if ts:
                text_chunks.append(ts)
    print("".join(text_chunks))


def docs_append(doc_id: str, text: str):
    service = svc_docs()
    # Insert at end index 1 (after start) using an append request
    requests_body = [{
        "insertText": {
            "location": {"index": 1e10},  # large index to approximate end
            "text": text + "\n"
        }
    }]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()
    print("Appended text.")


def main():
    parser = argparse.ArgumentParser(description="Google Drive/Sheets/Docs CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("init", help="Run OAuth flow and save token.json")

    d_list = sub.add_parser("drive_list", help="List files in a folder")
    d_list.add_argument("--folder-id", required=True)

    d_up = sub.add_parser("drive_upload", help="Upload a file into folder")
    d_up.add_argument("--folder-id", required=True)
    d_up.add_argument("--path", required=True)
    d_up.add_argument("--mime", required=False)

    d_dl = sub.add_parser("drive_download", help="Download a file by id")
    d_dl.add_argument("--file-id", required=True)
    d_dl.add_argument("--dest", required=True)

    s_read = sub.add_parser("sheets_read", help="Read a range from a sheet")
    s_read.add_argument("--sheet-id", required=True)
    s_read.add_argument("--range", required=True, dest="range_a1")

    s_app = sub.add_parser("sheets_append", help="Append a CSV row to a sheet range")
    s_app.add_argument("--sheet-id", required=True)
    s_app.add_argument("--range", required=True, dest="range_a1")
    s_app.add_argument("--values", required=True, help="Comma-separated values (e.g., 'a,b,c')")

    d_read = sub.add_parser("docs_read", help="Read text content from a Doc")
    d_read.add_argument("--doc-id", required=True)

    d_app = sub.add_parser("docs_append", help="Append text to a Doc")
    d_app.add_argument("--doc-id", required=True)
    d_app.add_argument("--text", required=True)

    args = parser.parse_args()

    if args.cmd == "init":
        get_credentials()
        print(f"Token saved to {TOKEN_PATH}")
        return

    if args.cmd == "drive_list":
        drive_list(args.folder_id)
    elif args.cmd == "drive_upload":
        drive_upload(args.folder_id, args.path, args.mime)
    elif args.cmd == "drive_download":
        drive_download(args.file_id, args.dest)
    elif args.cmd == "sheets_read":
        sheets_read(args.sheet_id, args.range_a1)
    elif args.cmd == "sheets_append":
        sheets_append(args.sheet_id, args.range_a1, args.values)
    elif args.cmd == "docs_read":
        docs_read(args.doc_id)
    elif args.cmd == "docs_append":
        docs_append(args.doc_id, args.text)
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()
