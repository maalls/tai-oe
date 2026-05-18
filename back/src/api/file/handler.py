"""File operations and upload handling."""

from pathlib import Path
from typing import Dict, Any
import traceback

from src.api.routes.helpers.server_response_helpers import send_error, send_text_response
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


def handle_prompt_get(handler, parsed_path: str, current_file: str):
    """Handle GET requests for prompt markdown content."""
    relative_path = parsed_path[len('/api/prompt/'):].strip('/')
    request_handlers = handler.request_handlers
    base_dir = Path(current_file).resolve().parents[1] / 'infrastructure' / 'prompts'
    try:
        content = request_handlers.handle_get_prompt_content(
            relative_path=relative_path,
            prompt_base_dir=base_dir,
        )
    except ValueError as e:
        return send_error(handler, 400, str(e))
    except FileNotFoundError as e:
        return send_error(handler, 404, str(e))
    except Exception as e:
        return send_error(handler, 500, f"Error reading prompt: {e}")

    return send_text_response(handler, 200, 'text/plain; charset=utf-8', content.encode('utf-8'))


def handle_storage_head(handler, storage_dir, parsed_path: str):
    """Handle HEAD requests for storage files."""
    raw_filename = parsed_path[len('/api/storage/'):]
    request_handlers = handler.request_handlers
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=False)
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        send_text_response(handler, 404, not_found['content_type'])
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
    request_handlers = handler.request_handlers
    try:
        storage_info = request_handlers.handle_storage_resolve_file(storage_dir, raw_filename)
    except FileNotFoundError:
        not_found = request_handlers.handle_storage_not_found_payload(raw_filename, include_body=True)
        print(f"[RAG] Storage request for file: {not_found['filename']}")
        print(f"[RAG] File not found in any storage location: {not_found['filename']}")
        send_text_response(handler, 404, not_found['content_type'], not_found['body'])
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
        send_text_response(handler, 500, error_payload['content_type'], error_payload['body'])
        return
