from types import SimpleNamespace

from src.api.email.routes import dispatch_email_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_email_routes_get_gmail_status(monkeypatch):
    calls = []

    def _fake(handler, qs):
        calls.append((handler, qs))

    monkeypatch.setattr("src.api.email.routes.handle_gmail_status_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/status")

    handled = dispatch_email_routes(handler, "GET", parsed, {"user_id": ["u-1"]}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, {"user_id": ["u-1"]})]


def test_dispatch_email_routes_post_extract_contact(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.email.routes.handle_email_extract_contact_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/email/extract-contact")

    handled = dispatch_email_routes(handler, "POST", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [handler]


def test_dispatch_email_routes_delete_email_regex(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.email.routes.handle_email_delete", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/email/e-1")

    handled = dispatch_email_routes(handler, "DELETE", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "e-1")]
