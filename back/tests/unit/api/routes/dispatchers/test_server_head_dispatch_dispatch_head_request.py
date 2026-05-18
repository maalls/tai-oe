from src.api.routes.dispatchers.server_head_dispatch import dispatch_head_request


class _HandlerStub:
    request_handlers = object()


def test_dispatch_head_request_returns_false_for_storage_path():
    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/storage/example.pdf")

    assert handled is False


def test_dispatch_head_request_returns_false_for_unknown_path():
    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/unknown")

    assert handled is False
