from src.api.routes.server_post_utility_handlers import handle_rfq_generate_post


class _RequestHandlersStub:
    def handle_rfq_generate(self, text, message_id, user_id):
        return {"status": "ok", "text": text, "message_id": message_id, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def _read_json(self, default=None):
        _ = default
        return {"content": "Need quote", "message_id": "m-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_rfq_generate_post_uses_content_fallback_and_user_id():
    handler = _HandlerStub()

    result = handle_rfq_generate_post(handler)

    assert result == ({"status": "ok", "text": "Need quote", "message_id": "m-1", "user_id": "u-1"}, 200)
