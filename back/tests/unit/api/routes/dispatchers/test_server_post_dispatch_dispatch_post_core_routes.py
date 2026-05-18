from src.api.routes.dispatchers.server_post_dispatch import dispatch_post_core_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_post_core_routes_products(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_post_dispatch.dispatch_product_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_post_core_routes(handler, "/api/products")

    assert handled is True
    assert calls == [(handler, "POST", "/api/products", {}, handler.request_handlers)]


def test_dispatch_post_core_routes_unknown_path(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_post_dispatch.dispatch_product_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = _HandlerStub()

    handled = dispatch_post_core_routes(handler, "/api/other")

    assert handled is False
