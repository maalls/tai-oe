from types import SimpleNamespace

from src.api.routes.dispatchers import server_get_dispatch


class _HandlerStub:
    def __init__(self):
        self.request_handlers = "rh"


def test_dispatch_get_request_calls_misc_group(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/prompt/opportunity/source")

    called = []
    monkeypatch.setattr(
        server_get_dispatch,
        "dispatch_get_misc_routes",
        lambda h, p, q: called.append((h, p.path, q)) or True,
    )

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True
    assert called == [(handler, "/api/prompt/opportunity/source", {})]


def test_dispatch_get_request_returns_false_when_nothing_matches(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/unknown")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: False)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is False
