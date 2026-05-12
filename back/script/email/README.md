# Gmail Unread Email Collector

Python script to connect to your Gmail account and collect unread emails using the Gmail API.

## Setup Instructions

### 1. Enable Gmail API in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Also enable the **Google Drive API** (for shared credentials):
   - Search for "Google Drive API"
   - Click "Enable"

### 2. Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure the OAuth consent screen if prompted:
   - User Type: External (for personal Gmail) or Internal (for workspace)
   - Add your email as a test user
   - Scopes: Gmail API read-only + Google Drive API read-only
4. Application type: **Desktop app**
5. Give it a name (e.g., "Gmail & Drive Collector")
6. Click "Create"
7. Download the credentials JSON file
8. **Important**: Save it to `back/var/credentials.json` (shared location for both Gmail and Drive)

### 3. Install Dependencies

```bash
cd back/script/email
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or add to your project's requirements.txt:

```
google-auth>=2.16.0
google-auth-oauthlib>=0.8.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.70.0
```

### 4. Run the Script

```bash
# Basic usage - collect 10 unread emails
python3 gmail_collector.py

# Collect more emails
MAX_EMAILS=50 python3 gmail_collector.py

# Use custom credentials file location
GMAIL_CREDENTIALS=/path/to/credentials.json python3 gmail_collector.py

# Save to custom output file
OUTPUT_FILE=my_emails.json python3 gmail_collector.py
```

**First run:** A browser window will open asking you to authorize the application. After authorization, a `token.pickle` file will be created for future runs.

## Usage in Your Code

```python
from gmail_collector import GmailCollector
    credentials_path="credentials.json",
    token_path="token.pickle"
)

# Authenticate (only needed once per session)
collector.authenticate()

# Get unread emails
emails = collector.get_unread_emails(max_results=20)

# Access email data
for email in emails:
    print(f"From: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body']}")

    # Mark as read if needed
    # collector.mark_as_read(email['id'])
```

## Advanced Queries

The script supports Gmail search queries:

```python
# Only emails from specific sender
emails = collector.get_unread_emails(query="is:unread from:example@gmail.com")

# Emails with specific subject
emails = collector.get_unread_emails(query="is:unread subject:invoice")

# Emails with attachments
emails = collector.get_unread_emails(query="is:unread has:attachment")

# Combine filters
emails = collector.get_unread_emails(query="is:unread from:boss@company.com subject:urgent")
```

## Output Format

Each email is a dictionary with:

- `id`: Gmail message ID
- `thread_id`: Thread ID (for conversations)
- `subject`: Email subject
- `from`: Sender address
- `to`: Recipient address
- `date`: Date sent
- `snippet`: Short preview
- `body`: Full email body (plain text when available)
- `labels`: Gmail labels (e.g., ["UNREAD", "INBOX"])

## Troubleshooting

**"Credentials file not found"**

- Make sure `credentials.json` is in the same directory as the script
- Or set `GMAIL_CREDENTIALS` env var to the full path

**"Access blocked: This app's request is invalid"**

- Make sure you added your email as a test user in OAuth consent screen
- Check that Gmail API is enabled

**"The user has not granted the app"**

- Delete `token.pickle` and re-authenticate

**Token expired**

- The script automatically refreshes expired tokens
- If issues persist, delete `token.pickle` and re-authenticate

## Security Notes

- **Never commit `credentials.json` or `token.pickle` to version control**
- Add them to `.gitignore`
- Keep credentials secure and don't share them
- The token gives read access to your Gmail account
