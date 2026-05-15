from types import SimpleNamespace

from src.api.opportunity.routes import dispatch_opportunity_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_opportunity_routes_get_search(monkeypatch):
    calls = []

    def _fake(handler, qs, request_handlers):
        calls.append((handler, qs, request_handlers))

    monkeypatch.setattr("src.api.opportunity.routes.handle_opportunities_search_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunities/search")

    handled = dispatch_opportunity_routes(handler, "GET", parsed, {"q": ["acme"]}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, {"q": ["acme"]}, handler.request_handlers)]


def test_dispatch_opportunity_routes_post_send_quote(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.opportunity.routes.handle_send_quote_for_opportunity_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunity/opp-1/send-quote")

    handled = dispatch_opportunity_routes(handler, "POST", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "opp-1")]


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
