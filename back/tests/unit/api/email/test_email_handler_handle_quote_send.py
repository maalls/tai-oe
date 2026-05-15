"""Tests for EmailHandlers.handle_quote_send."""

import json

from src.api.email.handler import EmailHandlers


class _PathStub:
    def __init__(self, path: str, existing_paths: set[str]):
        self.path = path
        self._existing_paths = existing_paths

    def __truediv__(self, other: str):
        next_path = f"{self.path}/{other}" if self.path else other
        return _PathStub(next_path, self._existing_paths)

    @property
    def parent(self):
        if "/" not in self.path:
            return _PathStub("", self._existing_paths)
        return _PathStub(self.path.rsplit("/", 1)[0], self._existing_paths)

    def exists(self):
        return self.path in self._existing_paths or self.path.endswith("/var/assets/quote_a.pdf")

    def __str__(self):
        return self.path


class _RepositoryStub:
    def __init__(self):
        self.calls = []

    def send_email(self, to: str, subject: str, body: str, attachment_path: str = None, cc: str = None):
        self.calls.append((to, subject, body, attachment_path, cc))
        return {"status": "ok", "message_id": "mid-1"}


def _make_handler():
    handler = EmailHandlers.__new__(EmailHandlers)
    handler._repository = _RepositoryStub()
    return handler


def test_handle_quote_send_success(monkeypatch):
    existing = set()

    def _path_factory(value):
        return _PathStub(str(value), existing)

    monkeypatch.setattr("src.api.email.handler.Path", _path_factory)

    handler = _make_handler()
    payload = {"pdf_filename": "quote_a.pdf", "email": "client@example.com", "body": "Bonjour"}

    result = handler.handle_quote_send(json.dumps(payload).encode("utf-8"), "application/json")

    assert result["status"] == "ok"
    assert result["message"] == "Quote emailed successfully"
    assert result["email"] == "client@example.com"
    assert len(handler._repository.calls) == 1
    to, subject, body, attachment_path, cc = handler._repository.calls[0]
    assert (to, subject, body, cc) == ("client@example.com", "Your Quote", "Bonjour", None)
    assert attachment_path.endswith("/var/assets/quote_a.pdf")


def test_handle_quote_send_missing_pdf_filename():
    handler = _make_handler()

    result = handler.handle_quote_send(b'{"email":"client@example.com"}', "application/json")

    assert result == {"status": "error", "message": "Missing pdf_filename"}
