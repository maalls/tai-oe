from src.api.routes.server_head_dispatch import dispatch_head_request


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_storage_head(self, parsed_path: str):
        self.calls.append(parsed_path)


def test_dispatch_head_request_routes_storage_path():
    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/storage/example.pdf")

    assert handled is True
    assert handler.calls == ["/api/storage/example.pdf"]


def test_dispatch_head_request_returns_false_for_unknown_path():
    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/unknown")

    assert handled is False
    assert handler.calls == []
