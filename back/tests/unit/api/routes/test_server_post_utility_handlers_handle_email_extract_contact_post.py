from src.api.routes.server_post_utility_handlers import handle_email_extract_contact_post


class _RequestHandlersStub:
    def handle_extract_contact_from_email(self, email_id, email_body, user_id):
        return {"status": "ok", "email_id": email_id, "email_body": email_body, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.headers = {"Authorization": "Bearer abc"}
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        _ = default
        return {"email_id": "e-1", "email_body": "hello"}

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


def test_handle_email_extract_contact_post_passes_optional_user_context():
    handler = _HandlerStub()

    result = handle_email_extract_contact_post(handler)

    assert result == ({"status": "ok", "email_id": "e-1", "email_body": "hello", "user_id": "u-1"}, 200)
