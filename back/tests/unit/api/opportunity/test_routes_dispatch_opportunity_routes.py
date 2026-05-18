from types import SimpleNamespace

from src.api.opportunity.routes import dispatch_opportunity_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_opportunity_routes_non_delete_returns_false():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunities/search")

    assert dispatch_opportunity_routes(handler, "GET", parsed, {"q": ["acme"]}, handler.request_handlers) is False
    assert dispatch_opportunity_routes(handler, "POST", parsed, {}, handler.request_handlers) is False


def test_dispatch_opportunity_routes_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.opportunity.routes.handle_opportunity_delete", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunities/opp-2")

    handled = dispatch_opportunity_routes(handler, "DELETE", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "opp-2")]
