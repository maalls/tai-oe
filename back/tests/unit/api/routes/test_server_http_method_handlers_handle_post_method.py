import src.api.routes.server_http_method_handlers as module
from src.api.routes.server_http_method_handlers import handle_post_method


class _HandlerStub:
    def __init__(self, path="/api/actions"):
        self.path = path
        self.errors = []

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message


def test_handle_post_method_returns_none_when_dispatched(monkeypatch):
    handler = _HandlerStub()

    monkeypatch.setattr(module, "dispatch_post_request", lambda _handler, _parsed: True)

    result = handle_post_method(handler)

    assert result is None


def test_handle_post_method_returns_404_when_not_dispatched(monkeypatch):
    handler = _HandlerStub()

    monkeypatch.setattr(module, "dispatch_post_request", lambda _handler, _parsed: False)

    result = handle_post_method(handler)

    assert result == (404, "Not found")
