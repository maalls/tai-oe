from types import SimpleNamespace

from src.api.routes.server_get_dispatch import dispatch_get_misc_routes


class _HandlerStub:
    def __init__(self):
        self.request_handlers = object()
        self.config = {"STORAGE_DIR": "/tmp"}
        self.calls = []

    def _handle_email_fetch_loop_status_get(self):
        self.calls.append("email_fetch_loop_status")


def test_dispatch_get_misc_routes_delegates_product_router(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_get_dispatch.dispatch_product_routes", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/products")

    handled = dispatch_get_misc_routes(handler, parsed, {"q": ["1"]})

    assert handled is True
    assert calls == [(handler, "GET", "/api/products", {"q": ["1"]}, handler.request_handlers)]


def test_dispatch_get_misc_routes_delegates_file_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.server_get_dispatch.dispatch_product_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_get_dispatch.dispatch_file_routes", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/storage/file.pdf")

    handled = dispatch_get_misc_routes(handler, parsed, {})

    assert handled is True
    assert calls == [(handler, "GET", "/api/storage/file.pdf", {}, handler.request_handlers)]
