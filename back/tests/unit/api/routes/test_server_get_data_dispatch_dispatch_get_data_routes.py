from types import SimpleNamespace

from src.api.routes.server_get_data_dispatch import dispatch_get_data_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_csv_get(self, parsed_path, qs):
        self.calls.append(("csv", parsed_path, qs))

    def _handle_quotes_list_get(self, request_handlers):
        self.calls.append(("quotes", request_handlers))


def test_dispatch_get_data_routes_csv_prefix_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/csv/query")

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["x"]}, request_handlers=object())

    assert handled is True
    assert handler.calls == [("csv", "/api/csv/query", {"q": ["x"]})]


def test_dispatch_get_data_routes_quotes_list_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quotes/list")
    request_handlers = object()

    handled = dispatch_get_data_routes(handler, parsed, {}, request_handlers=request_handlers)

    assert handled is True
    assert handler.calls == [("quotes", request_handlers)]
