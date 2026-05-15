from src.api.routes.server_post_utility_handlers import handle_opportunities_create_from_rfp_post


class _RequestHandlersStub:
    def handle_create_opportunity_from_rfp(self, body, content_type, user_id):
        return {"status": "ok", "content_type": content_type, "user_id": user_id, "body": body}


class _HandlerStub:
    def __init__(self):
        self.headers = {"Content-Type": "application/json", "Authorization": "Bearer abc"}
        self.request_handlers = _RequestHandlersStub()

    def _read_body(self):
        return b'{"rfp":1}'

    def _require_auth(self, auth_header=None, required=True):
        _ = auth_header
        _ = required
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_opportunities_create_from_rfp_post_uses_body_content_type_and_user():
    handler = _HandlerStub()

    result = handle_opportunities_create_from_rfp_post(handler)

    assert result == (
        {"status": "ok", "content_type": "application/json", "user_id": "u-1", "body": b'{"rfp":1}'},
        200,
    )
