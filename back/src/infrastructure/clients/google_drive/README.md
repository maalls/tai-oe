# Google Drive/Sheets/Docs CLI

A small tool to manage a Drive folder and edit Google Sheets/Docs.

## Setup

1. Create OAuth credentials (**Desktop app**, NOT service account) in Google Cloud Console:
   - Navigate to: **APIs & Services → Credentials**
   - Click **Create credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Download the JSON file
   - Save it to `var/gdrive/credentials.json` in this repo

   **Important**: The file must contain an `"installed"` key (Desktop app). Service account JSON will NOT work.

2. Enable APIs for your project:

- Google Drive API
- Google Sheets API
- Google Docs API

3. Install dependencies (inside your venv if you use one):

```bash
cd /opt/aioe/aioe
pip install -r requirements.txt
```

4. Run initial auth (opens browser, saves token):
   Use Python 3.

```bash
python3 scripts/gdrive_tool.py init
```

This creates `var/gdrive/token.json`.

## Usage

- List files in a Drive folder:

```bash
python3 scripts/gdrive_tool.py drive_list --folder-id <FOLDER_ID>
```

- Upload a file into the folder:

```bash
python3 scripts/gdrive_tool.py drive_upload --folder-id <FOLDER_ID> --path ./file.txt --mime text/plain
```

- Download a file by id:

```bash
python3 scripts/gdrive_tool.py drive_download --file-id <FILE_ID> --dest ./downloaded.bin
```

- Read a sheet range:

```bash
python3 scripts/gdrive_tool.py sheets_read --sheet-id <SPREADSHEET_ID> --range "Sheet1!A1:C10"
```

- Append a CSV row to a sheet:

```bash
python3 scripts/gdrive_tool.py sheets_append --sheet-id <SPREADSHEET_ID> --range "Sheet1!A1" --values "a,b,c"
```

- Read text from a Google Doc:

```bash
python3 scripts/gdrive_tool.py docs_read --doc-id <DOCUMENT_ID>
```

- Append text to a Google Doc:

```bash
python3 scripts/gdrive_tool.py docs_append --doc-id <DOCUMENT_ID> --text "Hello world"
```

## Notes

- Tokens are cached under `var/gdrive/token.json`.
- The CLI requests broad scopes to allow editing; reduce scopes if you want read-only.
- For server/headless environments, you can run the auth flow on a laptop, then copy `token.json` to the server.
