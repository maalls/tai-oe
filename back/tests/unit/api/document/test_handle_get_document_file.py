"""Unit tests for DocumentHandlers.handle_get_document_file."""

from pathlib import Path

import pytest

from src.api.document.handler import DocumentHandlers


def test_handle_get_document_file_reads_from_storage(tmp_path, monkeypatch):
    root = tmp_path / "src"
    storage_file = root / "var" / "storage" / "quotes" / "q.pdf"
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage_file.write_bytes(b"pdf-bytes")

    handler_module_dir = root / "api" / "document"
    handler_module_dir.mkdir(parents=True, exist_ok=True)
    fake_handler_file = handler_module_dir / "handler.py"
    fake_handler_file.write_text("# stub", encoding="utf-8")

    monkeypatch.setattr("src.api.document.handler.__file__", str(fake_handler_file))

    handler = DocumentHandlers()

    result = handler.handle_get_document_file("q.pdf")

    assert result == b"pdf-bytes"


def test_handle_get_document_file_rejects_path_traversal():
    handler = DocumentHandlers()

    with pytest.raises(ValueError):
        handler.handle_get_document_file("../secret.txt")


def test_handle_get_document_file_raises_when_missing(tmp_path, monkeypatch):
    root = tmp_path / "src"
    handler_module_dir = root / "api" / "document"
    handler_module_dir.mkdir(parents=True, exist_ok=True)
    fake_handler_file = handler_module_dir / "handler.py"
    fake_handler_file.write_text("# stub", encoding="utf-8")

    monkeypatch.setattr("src.api.document.handler.__file__", str(fake_handler_file))

    handler = DocumentHandlers()

    with pytest.raises(FileNotFoundError):
        handler.handle_get_document_file("missing.pdf")
