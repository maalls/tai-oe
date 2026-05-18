from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_mail_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_get_mail_routes_delegates_to_email_router(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/status")

    handled = dispatch_get_mail_routes(handler, parsed, {"user_id": ["u-1"]})

    assert handled is False
