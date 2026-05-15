import src.api.routes.server_http_method_handlers as module
from src.api.routes.server_http_method_handlers import handle_get_method


class _HandlerStub:
    def __init__(self, path="/api/csv/sources"):
        self.path = path
        self.errors = []

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message


def test_handle_get_method_returns_none_when_dispatched(monkeypatch):
    handler = _HandlerStub()

    monkeypatch.setattr(module, "dispatch_get_request", lambda _handler, _parsed, _qs: True)

    result = handle_get_method(handler)

    assert result is None


def test_handle_get_method_falls_back_to_static_serving(monkeypatch):
    handler = _HandlerStub(path="/index.html")

    monkeypatch.setattr(module, "dispatch_get_request", lambda _handler, _parsed, _qs: False)
    monkeypatch.setattr(module.http.server.SimpleHTTPRequestHandler, "do_GET", lambda _handler: "static")

    result = handle_get_method(handler)

    assert result == "static"
