from src.api.routes.server_get_misc_handlers import handle_fetch_get


class _RequestHandlersStub:
    def __init__(self):
        self.calls = []

    def handle_fetch_url(self, target_url, max_chars, timeout_ms):
        self.calls.append((target_url, max_chars, timeout_ms))
        return {"status": "ok", "url": target_url}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.errors = []
        self.json_calls = []

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message

    def _get_qs_int(self, qs, key, default):
        return int(qs.get(key, [default])[0])

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_fetch_get_validates_url_parameter():
    handler = _HandlerStub()

    result = handle_fetch_get(handler, {})

    assert result == (400, "Missing url parameter")


def test_handle_fetch_get_clamps_limits_and_calls_service():
    handler = _HandlerStub()

    result = handle_fetch_get(
        handler,
        {
            "url": ["https://example.org"],
            "max_chars": ["999999"],
            "timeout_ms": ["1"],
        },
    )

    assert result == ({"status": "ok", "url": "https://example.org"}, 200)
    assert handler.request_handlers.calls == [("https://example.org", 50000, 1000)]
