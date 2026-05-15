"""Unit test for DocumentHandlers.handle_delete_document."""

from src.api.document.handler import DocumentHandlers


class _Response:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _TableQuery:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self._op = None
        self._filters = {}

    def select(self, *_args, **_kwargs):
        self._op = "select"
        return self

    def delete(self):
        self._op = "delete"
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def maybe_single(self):
        return self

    def execute(self):
        if self._op == "select":
            doc_id = self._filters.get("id")
            return _Response(data=self.supabase.documents.get(doc_id))
        if self._op == "delete":
            doc_id = self._filters.get("id")
            self.supabase.deleted_ids.append(doc_id)
            return _Response(data=[{"id": doc_id}])
        return _Response(data=None)


class _SupabaseStub:
    def __init__(self, documents):
        self.documents = documents
        self.deleted_ids = []

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_delete_document_deletes_generic_document_and_file(tmp_path):
    storage_file = tmp_path / "doc_file.pdf"
    storage_file.write_bytes(b"x")

    supabase = _SupabaseStub(
        documents={
            "doc-2": {
                "id": "doc-2",
                "type": "RFP",
                "storage_key": "doc_file.pdf",
                "opportunity_id": "opp-1",
            }
        }
    )

    handler = DocumentHandlers(
        supabase=supabase,
        storage_path_resolver=lambda source, filename: storage_file,
    )

    result = handler.handle_delete_document("doc-2", user_id="u-1")

    assert result["status"] == "ok"
    assert supabase.deleted_ids == ["doc-2"]
    assert not storage_file.exists()
