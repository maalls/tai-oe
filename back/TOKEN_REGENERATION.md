# Google Token Regeneration Guide

## Quick Start

The simplest way to regenerate your Google tokens:

```bash
cd back/

# Regenerate Gmail token
./venv/bin/python regenerate_google_token.py

# Or regenerate Google Drive token
./venv/bin/python regenerate_google_token.py --type drive
```

A browser window will open. Complete the Google login, and your token will be automatically saved.

---

## Manual Regeneration (if helper script fails)

### Gmail Token

**Token location:** `back/var/token.pickle`

```bash
cd back/

# 1. Delete old token
rm -f var/token.pickle

# 2. Regenerate (opens browser for auth)
./venv/bin/python -c "from src.google_auth.google_auth import GoogleAPIClient; GoogleAPIClient().authenticate('gmail','v1')"
```

### Google Drive Token

**Token location:** `back/var/gdrive/token.json`

```bash
cd back/

# 1. Delete old token
rm -f var/gdrive/token.json

# 2. Regenerate (opens browser for auth)
./venv/bin/python -m src.google_drive.gdrive_tool init
```

---

## Troubleshooting

### "Gmail API forced" Error

This error means the token is missing or invalid. Run:

```bash
./venv/bin/python regenerate_google_token.py
```

### Network Error: "nodename nor servname provided"

- Check your internet connection
- Verify you can reach `https://oauth2.googleapis.com`
- Try again after the network is available

### "Credentials not found" Error

The credentials file is missing. You need to:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable APIs:
   - **Gmail API** (for email)
   - **Google Drive API** (for drive/sheets/docs)
   - **Google Sheets API** (for sheets)
4. Create OAuth 2.0 credentials:
   - Type: **Desktop app**
   - Download the JSON file
5. Save to the correct location:
   - **Gmail:** `back/var/credentials.json`
   - **Drive:** `back/var/gdrive/credentials.json`

### "Invalid credentials.json"

Make sure the file is:

- Downloaded from Google Cloud Console
- Type: **OAuth 2.0 Client ID (Desktop app)** ← NOT a service account
- Contains `"installed"` or `"web"` key (not `"type": "service_account"`)

### Browser Doesn't Open

If the browser fails to open automatically:

1. The command will print a URL in the terminal
2. Copy and manually open it in your browser
3. Complete the Google login
4. The token will be saved automatically

---

## When to Regenerate

Regenerate your token if:

- ✓ Token expired (API returns authorization error)
- ✓ Scopes changed (e.g., adding write access)
- ✓ Credentials rotated on Google Cloud Console
- ✓ Running on a new machine
- ✓ Token file corrupted or deleted

---

## Verify Token Works

After regenerating, verify the token is valid:

### Gmail

```bash
cd back/
./venv/bin/python -m src.command.fetch_emails --user-id <USER_ID>
```

### Google Drive

```bash
cd back/
./venv/bin/python -m src.google_drive.gdrive_tool drive list --folder-id <FOLDER_ID>
```

If successful, you should see emails or file listings.

---

## Token Details

| Service   | Credentials Path              | Token Path              | Command                                                     |
| --------- | ----------------------------- | ----------------------- | ----------------------------------------------------------- |
| **Gmail** | `var/credentials.json`        | `var/token.pickle`      | `./venv/bin/python regenerate_google_token.py`              |
| **Drive** | `var/gdrive/credentials.json` | `var/gdrive/token.json` | `./venv/bin/python regenerate_google_token.py --type drive` |

Both tokens are cached and reused automatically. Deleting the token forces re-authentication on the next use.

---

## References

- [Google Workspace API Docs](https://developers.google.com/workspace/guides)
- [Gmail API Quickstart](https://developers.google.com/gmail/api/quickstart)
- [Google Drive API Quickstart](https://developers.google.com/drive/api/quickstart)
