from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_misc_routes


class _HandlerStub:
    def __init__(self):
        self.request_handlers = object()
        self.config = {"STORAGE_DIR": "/tmp"}
        self.calls = []

    def _handle_prompt_get(self, parsed_path):
        self.calls.append(parsed_path)

def test_dispatch_get_misc_routes_delegates_prompt_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/prompt/mail/classify")

    handled = dispatch_get_misc_routes(handler, parsed, {})

    assert handled is True
    assert handler.calls == ["/api/prompt/mail/classify"]


def test_dispatch_get_misc_routes_returns_false_for_unknown_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/unknown")

    handled = dispatch_get_misc_routes(handler, parsed, {})

    assert handled is False
