from src.api.routes.server_get_misc_handlers import handle_email_fetch_loop_status_get


class _RequestHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_email_fetch_loop_status(self, status_path, legacy_path):
        self.calls.append((status_path, legacy_path))
        return {"status": "ok"}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_email_fetch_loop_status_get_uses_expected_paths():
    handler = _HandlerStub()

    result = handle_email_fetch_loop_status_get(
        handler,
        "/Users/malo/Documents/Projects/tai-oe/back/src/api/server.py",
    )

    assert result == ({"status": "ok"}, 200)
    status_path, legacy_path = handler.request_handlers.calls[0]
    assert str(status_path).endswith("/var/email_fetch_loop.json")
    assert str(legacy_path).endswith("/back/var/email_fetch_loop.json")
