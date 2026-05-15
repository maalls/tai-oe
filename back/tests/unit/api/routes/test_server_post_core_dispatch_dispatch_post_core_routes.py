from src.api.routes.server_post_core_dispatch import dispatch_post_core_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_products_post(self):
        self.calls.append("products")

    def _handle_fs_create_post(self):
        self.calls.append("fs_create")

    def _handle_fs_read_post(self):
        self.calls.append("fs_read")

    def _handle_curl_post(self):
        self.calls.append("curl")


def test_dispatch_post_core_routes_products():
    handler = _HandlerStub()

    handled = dispatch_post_core_routes(handler, "/api/products")

    assert handled is True
    assert handler.calls == ["products"]


def test_dispatch_post_core_routes_unknown_path():
    handler = _HandlerStub()

    handled = dispatch_post_core_routes(handler, "/api/other")

    assert handled is False
    assert handler.calls == []
