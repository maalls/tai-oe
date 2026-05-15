from src.api.routes.server_get_business_handlers import (
    handle_action_get,
    handle_quotes_download_get,
)


class _RequestHandlersStub:
    def handle_get_action(self, action_id, user_id):
        return {"status": "ok", "action_id": action_id, "user_id": user_id}


class _MatchStub:
    def __init__(self, value):
        self.value = value

    def group(self, index):
        assert index == 1
        return self.value


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def _require_auth_user_id(self):
        return "u-1"

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status

    def _handle_quote_download(self, filename, request_handlers, qs):
        return (filename, request_handlers, qs)


def test_handle_action_get_uses_match_group_and_auth_user():
    handler = _HandlerStub()

    result = handle_action_get(handler, _MatchStub("a-9"), handler.request_handlers)

    assert result == ({"status": "ok", "action_id": "a-9", "user_id": "u-1"}, 200)


def test_handle_quotes_download_get_extracts_filename():
    handler = _HandlerStub()

    result = handle_quotes_download_get(
        handler,
        "/api/quotes/download/quote-1.pdf",
        {"inline": ["1"]},
        handler.request_handlers,
    )

    assert result[0] == "quote-1.pdf"
    assert result[2] == {"inline": ["1"]}
