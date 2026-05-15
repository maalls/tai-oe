from types import SimpleNamespace

from src.api.routes.server_get_misc_dispatch import dispatch_get_misc_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_products_get(self, qs):
        self.calls.append(("products", qs))

    def _handle_storage_get(self, parsed_path):
        self.calls.append(("storage", parsed_path))


def test_dispatch_get_misc_routes_products_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/products")

    handled = dispatch_get_misc_routes(handler, parsed, {"q": ["1"]})

    assert handled is True
    assert handler.calls == [("products", {"q": ["1"]})]


def test_dispatch_get_misc_routes_storage_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/storage/file.pdf")

    handled = dispatch_get_misc_routes(handler, parsed, {})

    assert handled is True
    assert handler.calls == [("storage", "/api/storage/file.pdf")]
