"""Tests for QuoteSendService.handle_send_quote_for_opportunity."""

from datetime import datetime

from src.service.email.quote_send_service import QuoteSendService


class _PathStub:
    def __init__(self, path: str, exists_rule=None):
        self.path = path
        self._exists_rule = exists_rule or (lambda _p: False)

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


class _SendEmailStub:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
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


def test_handle_send_quote_for_opportunity_success():
    def _path_factory(value):
        return _PathStub(
            str(value),
            exists_rule=lambda p: p.endswith("var/storage/quotes/quote_1.pdf") or p.endswith("/var/storage/quotes/quote_1.pdf"),
        )

    supabase_calls = []
    sender = _SendEmailStub()
    service = QuoteSendService(
        send_email=sender,
        storage_path_resolver=lambda _source, filename: _PathStub(
            f"var/storage/quotes/{filename}",
            exists_rule=lambda p: p.endswith("var/storage/quotes/quote_1.pdf") or p.endswith("/var/storage/quotes/quote_1.pdf"),
        ),
        path_cls=_path_factory,
        supabase_factory=lambda: _SupabaseStub(supabase_calls),
        now_provider=lambda: datetime(2026, 5, 15, 10, 0, 0),
    )

    payload = {
        "to": ["a@example.com", "b@example.com"],
        "cc": ["c@example.com"],
        "subject": "Votre devis",
        "body": "Bonjour",
        "storage_key": "quote_1.pdf",
        "quote_id": "quote-1",
    }

    result = service.handle_send_quote_for_opportunity("opp-1", payload, user_id="u-1")

    assert result["status"] == "ok"
    assert result["message_id"] == "m-1"
    assert sender.calls[0]["to"] == "a@example.com, b@example.com"
    assert sender.calls[0]["cc"] == "c@example.com"
    assert sender.calls[0]["user_id"] == "u-1"
    assert any(call[0] == "document" and call[1] == "update" for call in supabase_calls)
    assert any(call[0] == "sent_email" and call[1] == "insert" for call in supabase_calls)
    assert any(call[0] == "opportunity" and call[1] == "update" for call in supabase_calls)


def test_handle_send_quote_for_opportunity_requires_to():
    sender = _SendEmailStub()
    service = QuoteSendService(
        send_email=sender,
        storage_path_resolver=lambda _source, _filename: _PathStub("", exists_rule=lambda _p: False),
    )

    result = service.handle_send_quote_for_opportunity(
        "opp-1",
        {"to": [], "subject": "s", "body": "b", "quote_id": "q-1"},
        user_id="u-1",
    )

    assert result == {"status": "error", "message": "At least one 'to' email is required"}
