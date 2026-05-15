from types import SimpleNamespace

from src.api.routes.server_get_action_download_dispatch import dispatch_get_action_download_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_action_get(self, match, request_handlers):
        self.calls.append(("action_get", match.group(1), request_handlers))

    def _handle_quotes_download_get(self, parsed_path, qs, request_handlers):
        self.calls.append(("quote_download", parsed_path, qs, request_handlers))


def test_dispatch_get_action_download_routes_action_get_regex():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-42")
    request_handlers = object()

    handled = dispatch_get_action_download_routes(handler, parsed, {}, request_handlers=request_handlers)

    assert handled is True
    assert handler.calls == [("action_get", "a-42", request_handlers)]


def test_dispatch_get_action_download_routes_quote_download_prefix():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quotes/download/file.pdf")
    request_handlers = object()

    handled = dispatch_get_action_download_routes(handler, parsed, {"inline": ["1"]}, request_handlers=request_handlers)

    assert handled is True
    assert handler.calls == [
        ("quote_download", "/api/quotes/download/file.pdf", {"inline": ["1"]}, request_handlers)
    ]
