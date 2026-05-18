from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_misc_routes


class _HandlerStub:
    def __init__(self):
        self.request_handlers = object()
        self.config = {"STORAGE_DIR": "/tmp"}
        self.calls = []

def test_dispatch_get_misc_routes_delegates_google_oauth_callback(monkeypatch):
    calls = []

    def _fake(handler, qs):
        calls.append((handler, qs))

    monkeypatch.setattr("src.api.routes.dispatchers.server_get_dispatch.handle_google_oauth_callback_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/google/oauth/callback")

    handled = dispatch_get_misc_routes(handler, parsed, {"code": ["abc"]})

    assert handled is True
    assert calls == [(handler, {"code": ["abc"]})]
