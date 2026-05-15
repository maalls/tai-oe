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


class _Response:
    def __init__(self, data):
        self.data = data


class _TableQuery:
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
        self.mode = None
        self.payload = None
        self.filters = {}

    def select(self, _fields):
        self.mode = "select"
        return self

    def update(self, payload):
        self.mode = "update"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def single(self):
        return self

    def execute(self):
        if self.table_name == "document" and self.mode == "select":
            doc_id = self.filters.get("id")
            return _Response(self.db.documents.get(doc_id))
        if self.table_name == "opportunity" and self.mode == "update":
            self.db.updates.append((self.table_name, self.payload, self.filters))
            return _Response([{"ok": True}])
        raise AssertionError(f"Unexpected query {self.table_name}:{self.mode}")


class _SupabaseStub:
    def __init__(self, documents):
        self.documents = documents
        self.updates = []

    def table(self, table_name: str):
        return _TableQuery(self, table_name)


def test_update_document_content_success_updates_file_and_opportunity_timestamp():
    supabase = _SupabaseStub(
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
        supabase=supabase,
        storage_dir_resolver=lambda _source: base_dir,
        now_provider=lambda: datetime(2026, 5, 15, 12, 0, 0),
    )

    result = service.update_document_content("doc-1", "new-content")

    assert result == {
        "status": "ok",
        "message": "Document content updated successfully",
        "document_id": "doc-1",
    }
    assert supabase.updates == [
        (
            "opportunity",
            {"updated_at": "2026-05-15T12:00:00"},
            {"id": "opp-1"},
        )
    ]


def test_update_document_content_returns_not_found_when_document_missing():
    service = DocumentContentService(
        supabase=_SupabaseStub({}),
        storage_dir_resolver=lambda _source: _PathStub("var/storage/rfp_uploads", set()),
    )

    result = service.update_document_content("missing", "x")

    assert result == {"status": "error", "message": "Document not found"}
