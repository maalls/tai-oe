from src.api.routes.server_post_utility_handlers import handle_curl_post


class _RequestHandlersStub:
    def handle_curl_request(self, **kwargs):
        return {"status": "ok", "method": kwargs["method"], "url": kwargs["target_url"]}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        _ = default
        return {
            "url": "https://example.org",
            "method": "post",
            "headers": {"X-Test": "1"},
            "body": "hello",
            "max_chars": 999999,
            "timeout_ms": 1,
        }

    def _get_payload_int(self, payload, key, default):
        return int(payload.get(key, default))

    def get_request_handlers(self):
        return self.request_handlers

    def _send_error(self, code, message):
        return code, message

    def json(self, payload, status=200):
        return payload, status


def test_handle_curl_post_clamps_limits_and_calls_service():
    handler = _HandlerStub()

    result = handle_curl_post(handler)

    assert result == ({"status": "ok", "method": "POST", "url": "https://example.org"}, 200)
