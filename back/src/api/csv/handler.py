"""CSV file request handlers."""

import json
from typing import Dict

from src.api.routes.server_body_helpers import read_body
from src.api.routes.server_response_helpers import send_error
from src.api.file.handler import FileHandler


class CsvHandlers:
    """Handlers for CSV file operations."""
    
    def __init__(self, file_handler: FileHandler):
        self.file_handler = file_handler
    
    def handle_list_files(self, qs: Dict) -> Dict:
        """Handle /api/csv/files request."""
        source = (qs.get('source') or [''])[0]
        if not source:
            raise ValueError("Missing 'source' parameter")
        
        files = self.file_handler.list_files_for_source(source)
        return {"files": files}
    
    def handle_sources(self) -> list:
        """Handle /api/csv/sources request."""
        return self.file_handler.list_sources()
    
    def handle_preview(self, qs: Dict) -> Dict:
        """Handle /api/csv/preview request."""
        if not qs.get('source') or not qs['source'][0]:
            raise ValueError("Missing 'source' parameter")
        if not qs.get('file') or not qs['file'][0]:
            raise ValueError("Missing 'file' parameter")
        
        source = qs['source'][0]
        sheet = qs['file'][0]
        
        target = self.file_handler.safe_file_from_query(source, sheet)
        
        # Parse optional filter params
        filter_raw = (qs.get('filter') or [None])[0]
        filters = None
        if filter_raw:
            filters = json.loads(filter_raw)
            if not isinstance(filters, dict):
                raise ValueError("filter must be a JSON object")
        
        limit = int((qs.get('limit') or ['100'])[0])
        offset = int((qs.get('offset') or ['0'])[0])
        limit = max(1, min(limit, 1000))
        offset = max(0, offset)
        
        return self.file_handler.csv_reader.read(target, offset=offset, limit=limit, filters=filters)
    
    def handle_raw(self, qs: Dict) -> bytes:
        """Handle /api/csv/raw request (returns file content bytes)."""
        source = (qs.get('source') or [None])[0]
        sheet = (qs.get('sheet') or [None])[0]
        
        if not source or not sheet:
            raise ValueError("Missing 'source' or 'sheet' parameter")
        
        target = self.file_handler.safe_file_from_query(source, sheet)
        return target.read_bytes()

    def handle_source_raw(self, qs: Dict) -> bytes:
        """Handle /api/csv/source request (returns source Excel file bytes)."""
        source = (qs.get('source') or [None])[0]
        if not source:
            raise ValueError("Missing 'source' parameter")

        candidate = (self.file_handler.storage_dir / source).resolve()
        if not candidate.exists() or candidate.suffix.lower() not in ('.xls', '.xlsx'):
            raise ValueError(f"Source file {candidate} not found or invalid")

        return candidate.read_bytes()


def handle_csv_source_post(handler):
    """Handle /api/csv/source POST endpoint."""
    content_type = handler.headers.get('Content-Type', '')
    body = read_body(handler)
    content_length = len(body)

    request_handlers = handler.request_handlers
    result = request_handlers.file_handler.handle_file_upload(content_type, content_length, body)
    return handler.json(result)


def handle_csv_get(handler, parsed_path: str, qs):
    """Handle /api/csv* GET endpoints."""
    request_handlers = handler.request_handlers

    if parsed_path == '/api/csv/files':
        return handle_csv_files_get(handler, qs, request_handlers)
    if parsed_path == '/api/csv/preview':
        return handle_csv_preview_get(handler, qs, request_handlers)
    if parsed_path == '/api/csv/raw':
        return handle_raw_stream(handler, qs, request_handlers)
    if parsed_path == '/api/csv/source':
        return handle_source_stream(handler, qs, request_handlers)
    if parsed_path == '/api/csv/download':
        return handle_csv_download(handler, qs, request_handlers)
    if parsed_path == '/api/csv/sources':
        return handle_csv_sources_get(handler, request_handlers)
    if parsed_path == '/api/csv/query':
        return handle_csv_query_get(handler, qs, request_handlers)
    if parsed_path.startswith('/api/csv/search'):
        return handle_csv_search_get(handler, qs, request_handlers)

    return None


def handle_csv_files_get(handler, qs, request_handlers):
    """Handle /api/csv/files GET endpoint."""
    return handler.json(request_handlers.csv_handlers.handle_list_files(qs))


def handle_csv_preview_get(handler, qs, request_handlers):
    """Handle /api/csv/preview GET endpoint."""
    return handler.json(request_handlers.csv_handlers.handle_preview(qs))


def handle_csv_sources_get(handler, request_handlers):
    """Handle /api/csv/sources GET endpoint."""
    return handler.json(request_handlers.csv_handlers.handle_sources())


def handle_csv_query_get(handler, qs, request_handlers):
    """Handle /api/csv/query GET endpoint."""
    return handler.json(request_handlers.database_handlers.handle_query(qs))


def handle_csv_search_get(handler, qs, request_handlers):
    """Handle /api/csv/search* GET endpoints."""
    return handler.json(request_handlers.database_handlers.handle_search(qs, request_handlers.embedding_generator))


def handle_raw_stream(handler, qs, request_handlers):
    """Stream raw CSV file."""
    try:
        content = request_handlers.csv_handlers.handle_raw(qs)
        handler.send_response(200)
        handler.send_header('Content-Type', 'text/csv; charset=utf-8')
        handler.send_header('Content-Length', str(len(content)))
        handler.end_headers()
        handler.wfile.write(content)
    except Exception as e:
        return send_error(handler, 500, f"Error streaming CSV: {e}")


def handle_source_stream(handler, qs, request_handlers):
    """Stream original Excel source file."""
    try:
        source = (qs.get('source') or [None])[0]
        if not source:
            return send_error(handler, 400, "Missing 'source' parameter")
        content = request_handlers.csv_handlers.handle_source_raw(qs)
        ext = source.lower().split('.')[-1] if '.' in source else ''
        content_type_map = {
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        handler.send_response(200)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Content-Disposition', f'attachment; filename="{source}"')
        handler.send_header('Content-Length', str(len(content)))
        handler.end_headers()
        handler.wfile.write(content)
    except Exception as e:
        return send_error(handler, 500, f"Error streaming source: {e}")


def handle_csv_download(handler, qs, request_handlers):
    """Download CSV file with proper filename."""
    try:
        source = (qs.get('source') or [None])[0]
        sheet = (qs.get('file') or [None])[0]

        if not source or not sheet:
            return send_error(handler, 400, "Missing 'source' or 'file' parameter")

        file_handler = request_handlers.file_handler
        csv_path = file_handler.safe_file_from_query(source, sheet)
        filename = sheet
        file_size = csv_path.stat().st_size

        handler.send_response(200)
        handler.send_header('Content-Type', 'text/csv; charset=utf-8')
        handler.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        handler.send_header('Content-Length', str(file_size))
        handler.end_headers()

        with open(csv_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                handler.wfile.write(chunk)
    except Exception as e:
        return send_error(handler, 500, f"Error downloading CSV: {e}")
