"""Tests for EmailHandlers.handle_send_quote_for_opportunity."""

from src.api.email.handler import EmailHandlers


class _PathStub:
    def __init__(self, path: str, exists_rule=None):
        self.path = path
        self._exists_rule = exists_rule or (lambda p: False)

    def __truediv__(self, other: str):
        return _PathStub(f"{self.path}/{other}" if self.path else other, self._exists_rule)

    @property
    def parent(self):
        if "/" not in self.path:
            return _PathStub("", self._exists_rule)
        return _PathStub(self.path.rsplit("/", 1)[0], self._exists_rule)

    def exists(self):
        return bool(self._exists_rule(self.path))

    def __str__(self):
        return self.path


class _RepositoryStub:
    def __init__(self):
        self.calls = []

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "ok", "message_id": "m-1", "provider": "gmail"}


class _Resp:
    def __init__(self, data):
        self.data = data
        self.error = None


class _TableOp:
    def __init__(self, table_name: str, recorder: list):
        self.table_name = table_name
        self.recorder = recorder

    def update(self, payload):
        self.recorder.append((self.table_name, "update", payload))
        return self

    def insert(self, payload):
        self.recorder.append((self.table_name, "insert", payload))
        return self

    def eq(self, field, value):
        self.recorder.append((self.table_name, "eq", field, value))
        return self

    def execute(self):
        return _Resp([{"ok": True}])


class _SupabaseStub:
    def __init__(self, recorder: list):
        self.recorder = recorder

    def table(self, name: str):
        return _TableOp(name, self.recorder)


def _make_handler():
    handler = EmailHandlers.__new__(EmailHandlers)
    handler._repository = _RepositoryStub()
    return handler


def test_handle_send_quote_for_opportunity_success(monkeypatch):
    def _path_factory(value):
        return _PathStub(
            str(value),
            exists_rule=lambda p: p.endswith("quote_1.pdf"),
        )

    monkeypatch.setattr("src.api.email.handler.Path", _path_factory)
    monkeypatch.setattr("src.api.email.handler.EmailHandlers._get_storage_path", staticmethod(lambda source, filename: _path_factory(f"var/storage/{source}s/{filename}")))

    supabase_calls = []
    monkeypatch.setattr(
        "src.api.email.handler.get_supabase_service",
        lambda: _SupabaseStub(supabase_calls),
    )

    handler = _make_handler()
    payload = {
        "to": ["a@example.com", "b@example.com"],
        "cc": ["c@example.com"],
        "subject": "Votre devis",
        "body": "Bonjour",
        "storage_key": "quote_1.pdf",
        "quote_id": "quote-1",
    }

    result = handler.handle_send_quote_for_opportunity("opp-1", payload, user_id="u-1")

    assert result["status"] == "ok"
    assert result["message_id"] == "m-1"
    assert handler._repository.calls[0]["to"] == "a@example.com, b@example.com"
    assert handler._repository.calls[0]["cc"] == "c@example.com"
    assert handler._repository.calls[0]["user_id"] == "u-1"
    assert any(call[0] == "document" and call[1] == "update" for call in supabase_calls)
    assert any(call[0] == "sent_email" and call[1] == "insert" for call in supabase_calls)
    assert any(call[0] == "opportunity" and call[1] == "update" for call in supabase_calls)


def test_handle_send_quote_for_opportunity_requires_to():
    handler = _make_handler()

    result = handler.handle_send_quote_for_opportunity(
        "opp-1",
        {"to": [], "subject": "s", "body": "b", "quote_id": "q-1"},
        user_id="u-1",
    )

    assert result == {"status": "error", "message": "At least one 'to' email is required"}
