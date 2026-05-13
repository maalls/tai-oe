# Google Drive Downloader

Download Google Sheets, Docs, Slides, and other files using the Google Drive API with OAuth2 authentication.

## Features

- ✅ Downloads Google Sheets as XLSX, CSV, PDF, ODS
- ✅ Downloads Google Docs as DOCX, PDF, ODT, TXT
- ✅ Downloads Google Slides as PPTX, PDF, ODP
- ✅ Downloads Google Drawings as PNG, PDF, SVG, JPG
- ✅ OAuth2 authentication with token persistence
- ✅ Automatic file type detection

## Setup

### 1. Shared Credentials Setup

**Important**: OAuth2 credentials are centralized in `back/var/credentials.json` and shared with Gmail collector.

If you haven't already:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable both APIs:
   - **Gmail API**: "APIs & Services" → "Library" → Search "Gmail API" → Enable
   - **Google Drive API**: "APIs & Services" → "Library" → Search "Google Drive API" → Enable

### 2. Create Combined OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose **Desktop application**
4. Name it something like "Gmail & Drive Collector"
5. Click "Create"
6. Download the credentials JSON
7. **Save to**: `back/var/credentials.json` (shared with Gmail)

### 3. First Run

```bash
python3 googledrive.py
```

- A browser window will open asking for permission
- Grant access to Gmail and Google Drive (read-only)
- The token will be saved as `back/var/token.pickle` for future runs

## Shared Credentials

Credentials are centralized in `back/var/`:

- `credentials.json` - OAuth2 client credentials
- `token.pickle` - Cached authentication token

Both Gmail and Google Drive modules use the same credentials file.

## Usage

```python
from script.vendors.googledrive.googledrive import GoogleDriveDownloader

downloader = GoogleDriveDownloader()

# Download a Google Sheet as XLSX
url = "https://docs.google.com/spreadsheets/d/YOUR_FILE_ID/edit"
xlsx_path = downloader.download(url, output_path="sheet.xlsx")

# Download as CSV
csv_path = downloader.download_sheets_as_csv(url, output_path="sheet.csv")

# Download a Google Doc as DOCX
doc_url = "https://docs.google.com/document/d/YOUR_FILE_ID/edit"
docx_path = downloader.download(doc_url, output_path="document.docx")

# Custom format
pptx_path = downloader.download(
    "https://docs.google.com/presentation/d/YOUR_FILE_ID/edit",
    output_path="slides.pptx",
    format_type="pptx"
)
```

## Supported Formats

### Google Sheets

- `xlsx` (default) - Excel format
- `csv` - Comma-separated values
- `ods` - OpenDocument Spreadsheet
- `pdf` - PDF

### Google Docs

- `docx` (default) - Word format
- `pdf` - PDF
- `odt` - OpenDocument Text
- `txt` - Plain text

### Google Slides

- `pptx` (default) - PowerPoint format
- `pdf` - PDF
- `odp` - OpenDocument Presentation

### Google Drawings

- `png` (default) - PNG image
- `pdf` - PDF
- `svg` - SVG vector
- `jpg` - JPEG image

## Token Refresh

If the token expires, delete `token.pickle` to generate a new one:

```bash
rm token.pickle
python3 googledrive.py
```

## Reusing Gmail Credentials

If you already have Gmail OAuth2 credentials:

1. Reuse `back/var/credentials.json`
2. Delete `token.pickle` (if it exists)
3. The first run will prompt for permissions including Google Drive

The credentials can be reused across both Gmail and Google Drive APIs.
