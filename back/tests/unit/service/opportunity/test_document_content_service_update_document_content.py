"""Tests for DocumentContentService.update_document_content."""

from datetime import datetime

from service.opportunity.document_content_service import DocumentContentService


class _PathStub:
    def __init__(self, path: str, existing_paths: set[str]):
        self.path = path
        self.existing_paths = existing_paths
        self.writes = {}

    def __truediv__(self, other: str):
        return _PathStub(f"{self.path}/{other}", self.existing_paths)

    def exists(self):
        return self.path in self.existing_paths

    def write_text(self, content: str, encoding: str = "utf-8"):
        self.writes[self.path] = (content, encoding)


class _DbHandlerStub:
    def __init__(self, documents):
        self.documents = documents
        self.updates = []

    def execute_dict_query(self, query, params=None):
        if "FROM document" in query:
            doc_id = params[0]
            document = self.documents.get(doc_id)
            return [document] if document else []
        raise AssertionError(f"Unexpected query: {query}")

    def execute_update(self, query, params=None):
        if query.strip().startswith("UPDATE opportunity"):
            self.updates.append((query, params))
            return 1
        raise AssertionError(f"Unexpected update query: {query}")


def test_update_document_content_success_updates_file_and_opportunity_timestamp():
    db_handler = _DbHandlerStub(
        {
            "doc-1": {
                "id": "doc-1",
                "storage_key": "rfp_1.txt",
                "opportunity_id": "opp-1",
            }
        }
    )
    existing_paths = {"var/storage/rfp_uploads/rfp_1.txt"}

    base_dir = _PathStub("var/storage/rfp_uploads", existing_paths)
    service = DocumentContentService(
        db_handler=db_handler,
        storage_dir_resolver=lambda _source: base_dir,
        now_provider=lambda: datetime(2026, 5, 15, 12, 0, 0),
    )

    result = service.update_document_content("doc-1", "new-content")

    assert result == {
        "status": "ok",
        "message": "Document content updated successfully",
        "document_id": "doc-1",
    }
    assert len(db_handler.updates) == 1
    assert db_handler.updates[0][1] == ("2026-05-15T12:00:00", "opp-1")


def test_update_document_content_returns_not_found_when_document_missing():
    service = DocumentContentService(
        db_handler=_DbHandlerStub({}),
        storage_dir_resolver=lambda _source: _PathStub("var/storage/rfp_uploads", set()),
    )

    result = service.update_document_content("missing", "x")

    assert result == {"status": "error", "message": "Document not found"}
