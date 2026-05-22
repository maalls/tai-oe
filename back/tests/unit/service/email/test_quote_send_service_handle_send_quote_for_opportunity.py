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


class _DbHandlerStub:
    def __init__(self, recorder: list):
        self.recorder = recorder

    def execute_update(self, query, params=None):
        self.recorder.append(("sql", " ".join(query.split()), params))
        return 1


def test_handle_send_quote_for_opportunity_success():
    def _path_factory(value):
        return _PathStub(
            str(value),
            exists_rule=lambda p: p.endswith("var/storage/quotes/quote_1.pdf") or p.endswith("/var/storage/quotes/quote_1.pdf"),
        )

    db_calls = []
    sender = _SendEmailStub()
    service = QuoteSendService(
        send_email=sender,
        storage_path_resolver=lambda _source, filename: _PathStub(
            f"var/storage/quotes/{filename}",
            exists_rule=lambda p: p.endswith("var/storage/quotes/quote_1.pdf") or p.endswith("/var/storage/quotes/quote_1.pdf"),
        ),
        path_cls=_path_factory,
        db_handler=_DbHandlerStub(db_calls),
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
    assert any("UPDATE document" in call[1] for call in db_calls)
    assert any("INSERT INTO sent_email" in call[1] for call in db_calls)
    assert any("UPDATE opportunity" in call[1] for call in db_calls)


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
