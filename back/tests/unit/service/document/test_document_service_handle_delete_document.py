"""Tests for DocumentService.handle_delete_document."""

from pathlib import Path

from service.document.document_service import DocumentService


class _DbHandler:
    def __init__(self, row):
        self.row = row
        self.update_calls = []

    def execute_dict_query(self, query, params=None):
        if "FROM document" in query:
            return [self.row] if self.row is not None else []
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        self.update_calls.append((query, params))
        return 1


def test_handle_delete_document_deletes_storage_and_row(tmp_path):
    doc_file = tmp_path / "quote.pdf"
    doc_file.write_bytes(b"pdf")

    service = DocumentService(
        db_handler=_DbHandler(
            {
                "id": "doc-1",
                "type": "QUOTE",
                "storage_key": "quote.pdf",
                "opportunity_id": "opp-1",
            }
        ),
        storage_path_resolver=lambda _source, _key: doc_file,
    )

    result = service.handle_delete_document("doc-1")

    assert result["status"] == "ok"
    assert result["message"] == "QUOTE deleted successfully"
    assert doc_file.exists() is False


def test_handle_delete_document_returns_not_found():
    service = DocumentService(
        db_handler=_DbHandler(None),
        storage_path_resolver=lambda _source, _key: Path("/tmp/missing"),
    )

    result = service.handle_delete_document("missing")

    assert result == {"status": "error", "message": "Document not found"}
