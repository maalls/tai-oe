# POST /api/csv/source Implementation

## Overview

Implemented the backend file upload endpoint to handle CSV/XLSX file imports from the frontend.

## Implementation Details

### Endpoint: `POST /api/csv/source`

- **Route**: `/api/csv/source`
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Response**: JSON with uploaded filename and path

### Backend Changes (rag.py)

1. **do_POST() method**

   - Routes POST requests to `/api/csv/source`
   - Catches exceptions and returns appropriate error responses

2. **\_handle_source_upload() method**

   - Validates `Content-Length` header
   - Verifies `Content-Type` is `multipart/form-data`
   - Extracts boundary from Content-Type header
   - Reads request body
   - Calls `_parse_multipart()` to extract file
   - Validates file extension (`.xlsx`, `.xls`, `.csv`)
   - Saves file to `STORAGE_DIR`
   - Returns JSON response with success status, source filename, and path

3. **\_parse_multipart() method**
   - Parses multipart form data by boundary
   - Extracts filename from Content-Disposition header
   - Extracts file content between headers and boundary
   - Returns tuple of (filename, file_data)

### Frontend Integration

The frontend already has the necessary JavaScript code:

- `openFileUpload()`: Shows hidden file input
- `handleFileUpload()`: POSTs file to `/api/csv/source` with FormData
- Automatically loads sources and sets current source on successful upload

### Response Format

```json
{
  "status": "ok",
  "source": "filename.csv",
  "path": "/full/path/to/var/storage/filename.csv"
}
```

### Error Handling

- Returns 400 if no file provided (Content-Length = 0)
- Returns 400 if Content-Type is not multipart/form-data
- Returns 400 if boundary not found
- Returns 400 if invalid file extension
- Returns 500 for other server errors with error message

### File Validation

Only accepts files with extensions:

- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- `.csv` (Comma-separated values)

### Storage

- Files are saved to `STORAGE_DIR` (configured via env or defaults to `var/storage`)
- Original filename is preserved
- If file already exists, it will be overwritten

## Testing

### Unit Tests Added

- `test_file_upload_saves_file()`: Validates multipart parsing and file extraction

### All Tests Status

✓ 9/9 tests passing

- test_get_groups_mapping PASSED
- test_etim_denormalizer PASSED
- test_get_sources_lists_excel_files PASSED
- test_get_sources_when_empty PASSED
- test_file_upload_saves_file PASSED
- test_csv_reader_reads_comma_delimited_file PASSED
- test_csv_reader_reads_semicolon_delimited_file PASSED
- test_csv_reader_returns_dict_with_headers_and_rows PASSED
- test_csv_reader_supports_offset_and_limit PASSED

## Integration Testing

Created `test_upload_integration.py` for manual testing against running server:

```bash
python back/test_upload_integration.py
```

## Usage Flow

1. User clicks "Upload" button in frontend (rag.html)
2. File input dialog opens via `openFileUpload()`
3. User selects CSV/XLSX file
4. Frontend calls `handleFileUpload()` which POSTs to `/api/csv/source`
5. Backend receives multipart request, parses, validates, and saves
6. Backend returns JSON with source name
7. Frontend automatically loads sources and displays uploaded file
