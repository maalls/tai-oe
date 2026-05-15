from types import SimpleNamespace

from src.api.invoice.routes import dispatch_invoice_routes


def test_dispatch_invoice_routes_post_quote_invoice(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.invoice.routes.handle_quote_invoice_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/quote/q-1/invoice")

    handled = dispatch_invoice_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [(handler, "q-1")]


def test_dispatch_invoice_routes_post_invoice_send(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.invoice.routes.handle_invoice_send_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/invoice/inv-1/send")

    handled = dispatch_invoice_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [(handler, "inv-1")]


def test_dispatch_invoice_routes_non_post_returns_false():
    handler = object()
    parsed = SimpleNamespace(path="/api/invoice/inv-1/send")

    handled = dispatch_invoice_routes(handler, "GET", parsed, {}, object())

    assert handled is False
