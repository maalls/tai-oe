from types import SimpleNamespace

from src.api.routes.server_get_mail_dispatch import dispatch_get_mail_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_gmail_status_get(self, qs):
        self.calls.append(("gmail_status", qs))

    def _handle_gmail_message_get(self, parsed_path):
        self.calls.append(("gmail_message", parsed_path))


def test_dispatch_get_mail_routes_gmail_status_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/status")

    handled = dispatch_get_mail_routes(handler, parsed, {"user_id": ["u-1"]})

    assert handled is True
    assert handler.calls == [("gmail_status", {"user_id": ["u-1"]})]


def test_dispatch_get_mail_routes_gmail_message_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/gmail/message/m-1")

    handled = dispatch_get_mail_routes(handler, parsed, {})

    assert handled is True
    assert handler.calls == [("gmail_message", "/api/gmail/message/m-1")]
