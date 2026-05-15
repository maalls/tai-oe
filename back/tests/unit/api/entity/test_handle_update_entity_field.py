"""Unit tests for EntityHandlers.handle_update_entity_field."""

from src.api.entity.handler import EntityHandlers


class _Response:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class _TableQuery:
    def __init__(self, supabase, table_name):
        self.supabase = supabase
        self.table_name = table_name
        self._payload = None
        self._filters = {}

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def execute(self):
        if self.supabase.mode == "error":
            return _Response(data=None, error="boom")
        if self.supabase.mode == "empty":
            return _Response(data=[])
        return _Response(data=[{"id": self._filters.get("id"), **(self._payload or {})}])


class _SupabaseStub:
    def __init__(self, mode="ok"):
        self.mode = mode

    def table(self, table_name):
        return _TableQuery(self, table_name)


def test_handle_update_entity_field_success():
    handler = EntityHandlers(supabase=_SupabaseStub(mode="ok"))

    result = handler.handle_update_entity_field(
        table="document",
        field="title",
        record_id="doc-1",
        value="New title",
        user_id="u-1",
    )

    assert result == {"status": "ok", "data": {"id": "doc-1", "title": "New title"}}


def test_handle_update_entity_field_validates_names_and_id():
    handler = EntityHandlers(supabase=_SupabaseStub(mode="ok"))

    assert handler.handle_update_entity_field("", "title", "doc-1", "v") == {
        "status": "error",
        "message": "Missing table or field",
    }
    assert handler.handle_update_entity_field("document", "bad-field", "doc-1", "v") == {
        "status": "error",
        "message": "Invalid table or field",
    }
    assert handler.handle_update_entity_field("document", "title", "", "v") == {
        "status": "error",
        "message": "Missing id",
    }


def test_handle_update_entity_field_handles_supabase_errors():
    err_handler = EntityHandlers(supabase=_SupabaseStub(mode="error"))
    empty_handler = EntityHandlers(supabase=_SupabaseStub(mode="empty"))

    err_result = err_handler.handle_update_entity_field("document", "title", "doc-1", "v")
    empty_result = empty_handler.handle_update_entity_field("document", "title", "doc-1", "v")

    assert err_result == {"status": "error", "message": "Failed to update: boom"}
    assert empty_result == {"status": "error", "message": "No rows updated"}
