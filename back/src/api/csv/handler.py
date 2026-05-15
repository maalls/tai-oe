"""CSV file request handlers."""

import json
from typing import Dict

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
    body = handler._read_body()
    content_length = len(body)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_csv_source_upload(content_type, content_length, body)
    return handler.json(result)
