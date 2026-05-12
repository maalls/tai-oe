# Send Quote Endpoint - 400 Error Fix

## Issue Identified

The `/api/opportunity/{id}/send-quote` endpoint was returning HTTP 400 errors when attempting to send quote emails with PDF attachments.

**Symptom**:

```
127.0.0.1 - - [03/Feb/2026 16:55:30] "POST /api/opportunity/9f33cdfe-b513-4e6a-bee4-0d633d2ec3d3/send-quote HTTP/1.1" 400 -
```

## Root Cause

The `handle_send_quote_for_opportunity()` method was looking for PDF files in the **wrong directory**.

**Incorrect Path**:

```python
assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
pdf_path = assets_dir / pdf_filename
```

**Correct Path** (where quote PDFs are actually stored):

```python
pdf_path = self._get_storage_path("quote", pdf_filename)
# Resolves to: var/storage/quotes/{pdf_filename}
```

## Fix Applied

Updated `handle_send_quote_for_opportunity()` in [back/src/controller/business_handler.py](back/src/controller/business_handler.py#L1245) to:

1. **Use correct storage directory**: Call `self._get_storage_path("quote", pdf_filename)` instead of hardcoded `/var/assets`
2. **Add diagnostic logging**: Log when PDF is found/not found, email parameters, and send results
3. **Improve error handling**: Properly format error responses when email sending fails

### Changes Made:

**Storage Path Fix**:

```python
# BEFORE
if pdf_filename:
    assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
    pdf_path = assets_dir / pdf_filename
    if not pdf_path.exists():
        return {"status": "error", "message": f"PDF file not found: {pdf_filename}"}

# AFTER
if pdf_filename:
    pdf_path = self._get_storage_path("quote", pdf_filename)
    if not pdf_path.exists():
        print(f"[BusinessHandlers] PDF not found at: {pdf_path}")
        return {"status": "error", "message": f"PDF file not found: {pdf_filename}"}
    print(f"[BusinessHandlers] Found PDF at: {pdf_path}")
```

**Diagnostic Logging**:

- Payload validation with parameter logging
- Email send debugging (recipients, subject, attachment path)
- Error result logging and formatting

**Better Error Response Handling**:

```python
else:
    print(f"[BusinessHandlers] Email send failed with result: {result}")
    if isinstance(result, dict) and result.get('status') == 'error':
        return result
    else:
        return {
            "status": "error",
            "message": result.get('message', 'Failed to send email') if isinstance(result, dict) else str(result)
        }
```

## Impact

✅ Quote PDFs are now correctly located and attached to emails  
✅ Better error messages for debugging  
✅ Proper HTTP 200 responses on success, 400 on validation/attachment failures

## Storage Directory Structure

Quote PDFs are organized as follows:

```
var/
└── storage/
    ├── quotes/        ← Quote PDFs (NOW USED)
    ├── rfp_uploads/   ← User-uploaded RFP documents
    ├── emails/        ← Email documents
    └── attachments/   ← Email/document attachments
```

The fix ensures the send-quote endpoint uses the correct `var/storage/quotes` directory where PDF generation stores its output.
