"""File operations and upload handling."""

from pathlib import Path
from typing import Dict, Any
import traceback

from src.api.routes.server_body_helpers import read_json
from src.api.routes.server_query_helpers import get_payload_int, get_qs_int
from src.lib.email.multipart import parse_multipart, extract_boundary_from_header
from src.lib.readers.xls import XlsReader


class FileHandler:
    """Handles file operations and conversions."""
    
    def __init__(self, storage_dir: Path, csv_reader):
        self.storage_dir = storage_dir
        self.csv_reader = csv_reader
    
    def safe_file_from_query(self, source: str, sheet: str) -> Path:
        """Resolve and validate file path from query parameters.
        
        Args:
            source: Source filename (e.g., "data.xlsx")
            sheet: CSV sheet name (e.g., "B01_COMMERCE.csv")
            
        Returns:
            Resolved file path
            
        Raises:
            ValueError: If file not found or invalid
        """
        name = source.rsplit('.', 1)[0]
        
        # First try the exact path
        candidate = (self.storage_dir / name / sheet).resolve()
        if candidate.exists() and candidate.suffix.lower() == '.csv':
            return candidate
        
        # If not found, search all directories for the sheet file
        # This handles encoding issues where UTF-8 gets mangled in URL parameters
        for dir_entry in self.storage_dir.iterdir():
            if not dir_entry.is_dir():
                continue
            # Check if this directory contains the requested sheet
            csv_path = dir_entry / sheet
            if csv_path.exists() and csv_path.suffix.lower() == '.csv':
                # Found it! Return this path
                return csv_path.resolve()
        
        # If still not found, raise error with the original path for debugging
        raise ValueError(f"File {candidate} not found or invalid")
    
    def list_sources(self) -> list:
        """List all Excel sources in storage directory."""
        files = sorted([p.name for p in self.storage_dir.glob('*.xls*')])
        return files
    
    def list_files_for_source(self, source: str) -> list:
        """List all CSV files for a given source."""
        source_dir = self.storage_dir / source.rsplit('.', 1)[0]
        
        if not source_dir.exists() or not source_dir.is_dir():
            return []
        
        return sorted([p.name for p in source_dir.glob('*.csv')])
    
    def convert_if_needed(self, file_path: Path) -> None:
        """Convert Excel file to CSV if needed.
        
        Args:
            file_path: Path to file
            
        Raises:
            RuntimeError: If conversion fails
        """
        ext = file_path.suffix.lower()
        if ext not in ('.xls', '.xlsx'):
            return

        output_dir = self.storage_dir / file_path.stem
        try:
            XlsReader.convertToCsv(file_path, output_dir)
        except Exception as e:
            raise RuntimeError(f"Failed to convert Excel to CSV: {e}")
    
    def handle_file_upload(self, content_type: str, content_length: int, body: bytes) -> Dict[str, Any]:
        """Process uploaded file.
        
        Args:
            content_type: Content-Type header
            content_length: Content length
            body: Request body
            
        Returns:
            Response dict with status and file info
            
        Raises:
            ValueError: If upload is invalid
        """
        if content_length == 0:
            raise ValueError("No file provided")

        if 'multipart/form-data' not in content_type:
            raise ValueError("Invalid content type")

        boundary = extract_boundary_from_header(content_type)
        if not boundary:
            raise ValueError("No boundary found")

        filename, file_data = parse_multipart(body, boundary)
        if not filename or not file_data:
            raise ValueError("No file data found")

        # Validate file extension
        valid_extensions = ('.xlsx', '.xls', '.csv')
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid file type. Allowed: {valid_extensions}")

        # Save file
        file_path = self.storage_dir / filename
        file_path.write_bytes(file_data)

        # Convert if needed
        self.convert_if_needed(file_path)

        return {"status": "ok", "source": filename, "path": str(file_path)}


def handle_fs_create_post(handler):
    """Handle /api/fs/create POST endpoint."""
    payload = read_json(handler, default={})
    raw_path = str(payload.get('path') or '').strip()
    kind = payload.get('type') or 'dir'

    target_path = handler._resolve_fs_path(raw_path)
    if target_path is None:
        return None

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fs_create(target_path=target_path, kind=kind)
    except Exception as e:
        return handler._send_error(500, f'Create failed: {e}')
    return handler.json(result)


def handle_fs_read_post(handler):
    """Handle /api/fs/read POST endpoint."""
    payload = read_json(handler, default={})
    raw_path = str(payload.get('path') or '').strip()

    max_chars = get_payload_int(payload, 'max_chars', 10000)
    max_chars = max(100, min(max_chars, 50000))

    target_path = handler._resolve_fs_path(raw_path)
    if target_path is None:
        return None

    if not target_path.exists() or not target_path.is_file():
        return handler._send_error(404, 'File not found')

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fs_read(target_path=target_path, max_chars=max_chars)
    except Exception as e:
        return handler._send_error(500, f'Read failed: {e}')
    return handler.json(result)


def handle_curl_post(handler):
    """Handle /api/curl POST endpoint."""
    payload = read_json(handler, default={})

    target_url = str(payload.get('url') or '').strip()
    if not target_url:
        return handler._send_error(400, 'Missing url')
    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        return handler._send_error(400, 'Invalid url scheme')

    method = str(payload.get('method') or 'GET').upper()
    if method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        return handler._send_error(400, 'Invalid method')

    headers = payload.get('headers') if isinstance(payload.get('headers'), dict) else {}
    body_text = payload.get('body') if isinstance(payload.get('body'), str) else None

    max_chars = get_payload_int(payload, 'max_chars', 10000)
    timeout_ms = get_payload_int(payload, 'timeout_ms', 8000)

    max_chars = max(100, min(max_chars, 50000))
    timeout_ms = max(1000, min(timeout_ms, 20000))

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_curl_request(
            target_url=target_url,
            method=method,
            headers=headers,
            body_text=body_text,
            max_chars=max_chars,
            timeout_ms=timeout_ms,
        )
        return handler.json(result)
    except Exception as e:
        return handler._send_error(500, f'Curl failed: {e}')


def handle_fetch_get(handler, qs):
    """Handle /api/fetch GET endpoint."""
    target_url = qs.get('url', [None])[0]
    if not target_url:
        return handler._send_error(400, 'Missing url parameter')

    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        return handler._send_error(400, 'Invalid url scheme')

    max_chars = get_qs_int(qs, 'max_chars', 10000)
    timeout_ms = get_qs_int(qs, 'timeout_ms', 8000)

    max_chars = max(100, min(max_chars, 50000))
    timeout_ms = max(1000, min(timeout_ms, 20000))

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fetch_url(
            target_url=target_url,
            max_chars=max_chars,
            timeout_ms=timeout_ms,
        )
        return handler.json(result)
    except Exception as e:
        return handler._send_error(500, f'Fetch failed: {e}')


def handle_prompt_get(handler, parsed_path: str, current_file: str):
    """Handle GET requests for prompt markdown content."""
    relative_path = parsed_path[len('/api/prompt/'):].strip('/')
    request_handlers = handler.get_request_handlers()
    base_dir = Path(current_file).resolve().parents[1] / 'infrastructure' / 'prompts'
    try:
        content = request_handlers.handle_get_prompt_content(
            relative_path=relative_path,
            prompt_base_dir=base_dir,
        )
    except ValueError as e:
        return handler._send_error(400, str(e))
    except FileNotFoundError as e:
        return handler._send_error(404, str(e))
    except Exception as e:
        return handler._send_error(500, f"Error reading prompt: {e}")

    return handler._send_text_response(200, 'text/plain; charset=utf-8', content.encode('utf-8'))


def handle_storage_head(handler, storage_dir, parsed_path: str):
    """Handle HEAD requests for storage files."""
    raw_filename = parsed_path[len('/api/storage/'):]
    request_handlers = handler.get_request_handlers()
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=False)
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        handler._send_text_response(404, not_found['content_type'])
        return

    filename = storage_info['filename']
    metadata = storage_info['metadata']

    print(f"[RAG] Storage HEAD request for file: {filename}")
    response_headers = request_handlers.handle_storage_response_headers(metadata)

    handler.send_response(200)
    for header_name, header_value in response_headers.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()


def handle_storage_get(handler, storage_dir, parsed_path: str):
    """Handle GET requests for storage files."""
    raw_filename = parsed_path[len('/api/storage/'):]
    request_handlers = handler.get_request_handlers()
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=True)
        print(f"[RAG] Storage request for file: {not_found['filename']}")
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        handler._send_text_response(404, not_found['content_type'], not_found['body'])
        return

    filename = storage_info['filename']
    storage_path = storage_info['storage_path']
    metadata = storage_info['metadata']

    print(f"[RAG] Storage request for file: {filename}")

    try:
        print(f"[RAG] Reading file: {storage_path}")
        response_headers = request_handlers.handle_storage_response_headers(metadata)

        handler.send_response(200)
        for header_name, header_value in response_headers.items():
            handler.send_header(header_name, header_value)
        handler.end_headers()

        for chunk in request_handlers.handle_storage_read_chunks(storage_path):
            handler.wfile.write(chunk)
        print(f"[RAG] File sent successfully: {filename} ({metadata['file_size']} bytes)")
        return
    except Exception as error:
        print(f"[RAG] Error reading file {filename}: {error}")
        traceback.print_exc()
        error_payload = request_handlers.handle_storage_read_error_payload(error)
        handler._send_text_response(500, error_payload['content_type'], error_payload['body'])
        return
