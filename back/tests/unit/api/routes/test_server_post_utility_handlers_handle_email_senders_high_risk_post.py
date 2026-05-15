from src.api.routes.server_post_utility_handlers import handle_email_senders_high_risk_post


class _RequestHandlersStub:
    def handle_get_high_risk_senders(self, user_id):
        return {"status": "ok", "user_id": user_id, "items": []}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_email_senders_high_risk_post_uses_authenticated_user_id():
    handler = _HandlerStub()

    result = handle_email_senders_high_risk_post(handler)

    assert result == ({"status": "ok", "user_id": "u-1", "items": []}, 200)
