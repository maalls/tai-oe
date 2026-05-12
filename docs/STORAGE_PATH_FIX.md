# Storage Path Consolidation - Send Quote 400 Error Fix

## Problem Identified

The send-quote endpoint was returning 400 errors because PDF generation and retrieval were using **completely different storage paths**:

```
PDF Generation (_generate_quote_pdf):  var/assets/quote_*.pdf
PDF Retrieval (send_quote):            var/storage/quotes/quote_*.pdf
```

Result: "PDF file not found" when trying to send quotes.

## Root Cause Analysis

The codebase had evolved with two separate storage strategies that were never consolidated:

1. **Old path**: `var/assets/` - legacy general assets directory
2. **New path**: `var/storage/{type}/` - organized by document type (quotes, rfp_uploads, attachments, etc.)

The send-quote endpoint was updated to the new structure, but PDF generation was overlooked.

## Solution Applied

### Fix 1: PDF Generation (Line 701)

Changed `_generate_quote_pdf()` to use consistent storage structure:

```python
# BEFORE - Using old /var/assets path
assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
pdf_path = assets_dir / pdf_filename

# AFTER - Using new organized structure
storage_dir = self._get_storage_dir("quote")  # Resolves to: var/storage/quotes/
pdf_path = storage_dir / pdf_filename
```

### Fix 2: PDF Retrieval (Line 1254)

Already fixed in previous commit - send_quote now uses:

```python
pdf_path = self._get_storage_path("quote", pdf_filename)  # → var/storage/quotes/
```

## Unified Storage Architecture

```
var/storage/
├── quotes/          ← Quote PDFs (NOW UNIFIED)
├── rfp_uploads/     ← RFP documents from source page
├── emails/          ← Email documents
└── attachments/     ← Email/document attachments
```

All paths go through `_get_storage_dir()` and `_get_storage_path()` helper methods.

## Impact

✅ **PDF generation** and **PDF retrieval** now use identical paths  
✅ **File lookup** succeeds - send-quote endpoint works  
✅ **Storage is organized** by document type  
✅ **Maintainability** improved - single source of truth for paths  
✅ **Future-proof** - easy to add new document types

## Testing Verification

The quote send flow now works end-to-end:

1. Generate PDF → saved to `var/storage/quotes/quote_20260203_164814_6e8ade27.pdf` ✓
2. Store storage_key in database ✓
3. Send quote → retrieves from same `var/storage/quotes/` path ✓
4. File found and attached ✓
5. Email sent with HTTP 200 ✓

## Files Modified

- `back/src/controller/business_handler.py`
  - Line ~701: `_generate_quote_pdf()` - PDF generation path
  - Line ~1254: `handle_send_quote_for_opportunity()` - PDF retrieval path (from previous fix)
