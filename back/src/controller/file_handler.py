"""File operations and upload handling."""

from pathlib import Path
from typing import Dict, Any

from src.reader.xls import XlsReader
from src.controller.multipart import parse_multipart, extract_boundary_from_header


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
