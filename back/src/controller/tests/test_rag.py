import sys
import types
from pathlib import Path
import pandas as pd

import pytest

# Provide a lightweight stub for the embeddings module so rag.rag imports cleanly during tests
sys.modules.setdefault("embeddings", types.SimpleNamespace(EmbeddingGenerator=lambda: None))

from src.controller.rag import make_handler


def _build_handler(storage_dir: Path):
    handler_cls = make_handler({"STORAGE_DIR": storage_dir})
    handler = handler_cls.__new__(handler_cls)
    handler.config = {"STORAGE_DIR": storage_dir}
    return handler


def test_get_sources_lists_excel_files(tmp_path: Path):
    (tmp_path / "b_file.xls").write_text("data")
    (tmp_path / "a_file.xlsx").write_text("data")
    (tmp_path / "ignore.csv").write_text("data")

    handler = _build_handler(tmp_path)
    files = handler.get_request_handlers().handle_sources()

    assert files == ["a_file.xlsx", "b_file.xls"]


def test_get_sources_when_empty(tmp_path: Path):
    handler = _build_handler(tmp_path)

    files = handler.get_request_handlers().handle_sources()

    assert files == []


def test_file_upload_saves_file(tmp_path: Path):
    """Test that _parse_multipart correctly extracts filename and file data"""
    handler = _build_handler(tmp_path)
    file_handler = handler.get_request_handlers().file_handler
    
    # Create a valid multipart form data request
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"test,data\n1,2\n3,4"
    filename = "test_file.csv"
    
    # Build multipart body
    body = (
        f'------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: text/csv\r\n'
        f'\r\n'
    ).encode() + file_content + b'\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--'
    
    result = file_handler.handle_file_upload(
        content_type=f"multipart/form-data; boundary={boundary}",
        content_length=len(body),
        body=body,
    )

    assert result["status"] == "ok"
    saved_path = Path(result["path"])
    assert saved_path.exists()
    assert saved_path.read_bytes() == file_content


def test_uploaded_excel_is_converted_to_csv(tmp_path: Path):
    handler = _build_handler(tmp_path)
    file_handler = handler.get_request_handlers().file_handler

    # Build a simple Excel file with two sheets: hello and world
    xlsx_path = tmp_path / "sample.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame({"a": [1, 2]}).to_excel(writer, sheet_name="hello", index=False)
        pd.DataFrame({"b": [3, 4]}).to_excel(writer, sheet_name="world", index=False)

    # Simulate post-processing after upload
    file_handler.convert_if_needed(xlsx_path)

    output_dir = tmp_path / "sample"
    csv_files = {p.name for p in output_dir.glob("*.csv")}

    assert csv_files == {"hello.csv", "world.csv"}
