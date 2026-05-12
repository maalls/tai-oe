# Gmail Integration for Quote Sending

## Implementation Summary

The `/api/quote/send` endpoint has been successfully implemented to send quotes via Gmail with PDF attachments.

## Backend Components

### 1. GmailClient (`src/rag/gmail_client.py`)

- OAuth2 authentication using existing Google credentials
- Sends emails with PDF attachments
- Reuses `var/gdrive/credentials.json` and `var/gdrive/token.json`
- Scopes: `gmail.send`, `drive`, `spreadsheets`

### 2. BusinessHandlers (`src/rag/business_handler.py`)

- Added `handle_quote_send()` method
- Validates PDF existence and email parameters
- Instantiates GmailClient with proper credentials
- Returns identifiable error codes for auth/permission issues

### 3. RequestHandlers (`src/rag/handlers.py`)

- Added `handle_quote_send()` wrapper method

### 4. Server Routes (`src/rag/rag.py`)

- Added POST `/api/quote/send` route

## API Endpoint

### POST /api/quote/send

**Request Body:**

```json
{
  "pdf_filename": "quote_20250116_123456_abc123.pdf",
  "email": "customer@example.com",
  "body": "Hi, here is the quote"
}
```

**Success Response:**

```json
{
  "status": "ok",
  "message": "Quote emailed successfully",
  "email": "customer@example.com",
  "message_id": "18d1234567890abcd"
}
```

**Error Responses:**

1. Missing required fields:

```json
{
  "status": "error",
  "message": "Missing pdf_filename" // or "Missing email address"
}
```

2. PDF not found:

```json
{
  "status": "error",
  "message": "Quote PDF not found: filename.pdf"
}
```

3. Gmail authentication error:

```json
{
  "status": "error",
  "error_code": "GMAIL_AUTH_ERROR",
  "message": "Please authorize Gmail access"
}
```

4. Gmail permission error:

```json
{
  "status": "error",
  "error_code": "GMAIL_PERMISSION_ERROR",
  "message": "Insufficient permissions to send email"
}
```

## First-Time Setup

When the endpoint is called for the first time, if the `gmail.send` scope hasn't been authorized:

1. The backend will trigger the OAuth consent flow
2. A browser window will open asking for Gmail permissions
3. After granting permission, the token.json will be updated with the new scopes
4. Subsequent calls will work without user intervention

## Frontend Integration

The frontend (`BusinessPage.vue`) already includes:

- Email input field
- Email body textarea (default: "Hi, here is the quote")
- `sendQuoteEmail()` function that POSTs to `/api/quote/send`
- Error handling for identifiable error codes

## Testing

1. Generate a quote to create a PDF
2. Enter an email address
3. Optionally edit the email body
4. Click "Email Quote"
5. On first use, authorize Gmail access when prompted
6. Email should be sent with PDF attached

## Error Handling

The frontend should check for `error_code` in responses:

- `GMAIL_AUTH_ERROR`: Display OAuth prompt message
- `GMAIL_PERMISSION_ERROR`: Display permission denied message
- Other errors: Display generic error message

## Security Notes

- PDF filenames are validated to prevent path traversal
- Only files in `var/assets/` with `quote_*.pdf` pattern can be sent
- Uses existing OAuth2 credentials from Google Drive integration
- Token refresh is handled automatically
