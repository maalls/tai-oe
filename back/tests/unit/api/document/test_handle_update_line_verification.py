"""Unit tests for DocumentHandlers.handle_update_line_verification."""

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
        self._payload = None
        self._filters = {}
        self._fields = None

    def select(self, fields):
        self._op = "select"
        self._fields = fields
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def single(self):
        return self

    def execute(self):
        if self.table_name == "document" and self._op == "select":
            if self._filters.get("id") == "doc-1":
                return _Response(data={"id": "doc-1"})
            return _Response(data=None)

        if self.table_name == "document_line" and self._op == "select":
            if self._fields == "id, position, document_id":
                return _Response(data=[{"id": "line-1", "document_id": "doc-1", "position": 1}])
            return _Response(data=[self.supabase.updated_line])

        if self.table_name == "document_line" and self._op == "update":
            self.supabase.updated_line = {
                "document_id": self._filters.get("document_id"),
                "position": self._filters.get("position"),
                **(self._payload or {}),
            }
            return _Response(data=[self.supabase.updated_line])

        return _Response(data=[])


class _SupabaseStub:
    def __init__(self):
        self.updated_line = {"document_id": "doc-1", "position": 1, "is_ref_verified": False}

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_update_line_verification_success_with_fields():
    handler = DocumentHandlers(supabase=_SupabaseStub())

    result = handler.handle_update_line_verification(
        document_id="doc-1",
        line_index=1,
        verification_fields={"is_ref_verified": True, "is_quantity_verified": True},
        user_id="u-1",
    )

    assert result == {"status": "ok"}


def test_handle_update_line_verification_supports_backward_is_ref_verified():
    handler = DocumentHandlers(supabase=_SupabaseStub())

    result = handler.handle_update_line_verification(
        document_id="doc-1",
        line_index=1,
        verification_fields=None,
        is_ref_verified=True,
        user_id="u-1",
    )

    assert result == {"status": "ok"}


def test_handle_update_line_verification_requires_fields():
    handler = DocumentHandlers(supabase=_SupabaseStub())

    result = handler.handle_update_line_verification(
        document_id="doc-1",
        line_index=1,
        verification_fields=None,
        is_ref_verified=None,
        user_id="u-1",
    )

    assert result == {"status": "error", "message": "No verification fields provided"}
