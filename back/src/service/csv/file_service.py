"""CSV file upload service for FastAPI transport."""

from pathlib import Path
from typing import Any, Dict

from src.lib.readers.xls import XlsReader


class CsvFileService:
    """Handle uploaded source files and optional Excel to CSV conversion."""

    def __init__(self, storage_dir: Path, csv_reader):
        self.storage_dir = storage_dir
        self.csv_reader = csv_reader

    def safe_file_from_query(self, source: str, sheet: str) -> Path:
        name = source.rsplit(".", 1)[0]
        candidate = (self.storage_dir / name / sheet).resolve()
        if candidate.exists() and candidate.suffix.lower() == ".csv":
            return candidate

        for dir_entry in self.storage_dir.iterdir():
            if not dir_entry.is_dir():
                continue
            csv_path = dir_entry / sheet
            if csv_path.exists() and csv_path.suffix.lower() == ".csv":
                return csv_path.resolve()

        raise ValueError(f"File {candidate} not found or invalid")

    def read_source_file(self, source: str) -> bytes:
        candidate = (self.storage_dir / source).resolve()
        if not candidate.exists() or candidate.suffix.lower() not in (".xls", ".xlsx"):
            raise ValueError(f"Source file {candidate} not found or invalid")
        return candidate.read_bytes()

    def list_sources(self) -> list:
        return sorted([p.name for p in self.storage_dir.glob("*.xls*")])

    def list_files_for_source(self, source: str) -> list:
        source_dir = self.storage_dir / source.rsplit(".", 1)[0]
        if not source_dir.exists() or not source_dir.is_dir():
            return []
        return sorted([p.name for p in source_dir.glob("*.csv")])

    def convert_if_needed(self, file_path: Path) -> None:
        ext = file_path.suffix.lower()
        if ext not in (".xls", ".xlsx"):
            return

        output_dir = self.storage_dir / file_path.stem
        try:
            XlsReader.convertToCsv(file_path, output_dir)
        except Exception as exc:
            raise RuntimeError(f"Failed to convert Excel to CSV: {exc}")

    def handle_uploaded_file(self, filename: str, file_data: bytes) -> Dict[str, Any]:
        if not filename or not file_data:
            raise ValueError("No file data found")

        valid_extensions = (".xlsx", ".xls", ".csv")
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"Invalid file type. Allowed: {valid_extensions}")

        file_path = self.storage_dir / filename
        file_path.write_bytes(file_data)
        self.convert_if_needed(file_path)

        return {"status": "ok", "source": filename, "path": str(file_path)}
