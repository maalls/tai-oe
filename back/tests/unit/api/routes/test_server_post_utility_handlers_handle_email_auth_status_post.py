from src.api.routes.server_post_utility_handlers import handle_email_auth_status_post


class _RequestHandlersStub:
    def handle_get_email_auth_status(self, email_id, user_id):
        return {"status": "ok", "email_id": email_id, "user_id": user_id}


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


def test_handle_email_auth_status_post_extracts_email_id_and_user_id():
    handler = _HandlerStub()

    result = handle_email_auth_status_post(handler, "/api/email/auth/e-1")

    assert result == ({"status": "ok", "email_id": "e-1", "user_id": "u-1"}, 200)
