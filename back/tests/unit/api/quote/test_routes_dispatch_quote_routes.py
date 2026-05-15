from types import SimpleNamespace

from src.api.quote.routes import dispatch_quote_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_quote_routes_get_list(monkeypatch):
    calls = []

    def _fake(handler, request_handlers):
        calls.append((handler, request_handlers))

    monkeypatch.setattr("src.api.quote.routes.handle_quotes_list_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quotes/list")

    handled = dispatch_quote_routes(handler, "GET", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, handler.request_handlers)]


def test_dispatch_quote_routes_post_send(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.quote.routes.handle_quote_send_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quote/send")

    handled = dispatch_quote_routes(handler, "POST", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [handler]


def test_dispatch_quote_routes_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.quote.routes.handle_quote_delete", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quote/q-1")

    handled = dispatch_quote_routes(handler, "DELETE", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "q-1")]
