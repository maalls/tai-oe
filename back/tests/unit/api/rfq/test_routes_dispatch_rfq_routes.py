from types import SimpleNamespace

from src.api.rfq.routes import dispatch_rfq_routes


def test_dispatch_rfq_routes_post_generate(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.rfq.routes.handle_rfq_generate_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/rfq/generate")

    handled = dispatch_rfq_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [handler]


def test_dispatch_rfq_routes_post_rfp(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.rfq.routes.handle_rfp_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/rfp")

    handled = dispatch_rfq_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [handler]
