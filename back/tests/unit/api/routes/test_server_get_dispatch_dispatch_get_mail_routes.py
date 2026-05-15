from types import SimpleNamespace

from src.api.routes.server_get_dispatch import dispatch_get_mail_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_get_mail_routes_delegates_to_email_router(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_get_dispatch.dispatch_email_routes", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/status")

    handled = dispatch_get_mail_routes(handler, parsed, {"user_id": ["u-1"]})

    assert handled is True
    assert calls == [(handler, "GET", "/api/gmail/status", {"user_id": ["u-1"]}, handler.request_handlers)]
