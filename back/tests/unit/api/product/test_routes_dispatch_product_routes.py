from types import SimpleNamespace

from src.api.product.routes import dispatch_product_routes


def test_dispatch_product_routes_get(monkeypatch):
    calls = []

    def _fake(handler, qs):
        calls.append((handler, qs))

    monkeypatch.setattr("src.api.product.routes.handle_products_get", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/products")

    handled = dispatch_product_routes(handler, "GET", parsed, {"q": ["x"]}, object())

    assert handled is True
    assert calls == [(handler, {"q": ["x"]})]


def test_dispatch_product_routes_post(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.product.routes.handle_products_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/products")

    handled = dispatch_product_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [handler]
