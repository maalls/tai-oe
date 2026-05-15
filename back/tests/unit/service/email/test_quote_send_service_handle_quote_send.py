"""Tests for QuoteSendService.handle_quote_send."""

import json

from src.service.email.quote_send_service import QuoteSendService


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


class _SendEmailStub:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "ok", "message_id": "mid-1"}


def test_handle_quote_send_success():
    existing = set()

    def _path_factory(value):
        return _PathStub(str(value), existing)

    sender = _SendEmailStub()
    service = QuoteSendService(
        send_email=sender,
        storage_path_resolver=lambda _source, _filename: _PathStub("", existing),
        path_cls=_path_factory,
    )
    payload = {"pdf_filename": "quote_a.pdf", "email": "client@example.com", "body": "Bonjour"}

    result = service.handle_quote_send(json.dumps(payload).encode("utf-8"), "application/json")

    assert result["status"] == "ok"
    assert result["message"] == "Quote emailed successfully"
    assert result["email"] == "client@example.com"
    assert len(sender.calls) == 1
    sent = sender.calls[0]
    assert sent["to"] == "client@example.com"
    assert sent["subject"] == "Your Quote"
    assert sent["body"] == "Bonjour"
    assert sent["attachment_path"].endswith("/var/assets/quote_a.pdf")


def test_handle_quote_send_missing_pdf_filename():
    sender = _SendEmailStub()
    service = QuoteSendService(
        send_email=sender,
        storage_path_resolver=lambda _source, _filename: None,
    )

    result = service.handle_quote_send(b'{"email":"client@example.com"}', "application/json")

    assert result == {"status": "error", "message": "Missing pdf_filename"}
