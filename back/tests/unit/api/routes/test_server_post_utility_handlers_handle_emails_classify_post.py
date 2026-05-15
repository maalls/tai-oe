from src.api.routes.server_post_utility_handlers import handle_emails_classify_post


class _RequestHandlersStub:
    def handle_classify_email(self, email_uuid, user_id, force):
        return {"status": "ok", "email_uuid": email_uuid, "user_id": user_id, "force": force}


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


def test_handle_emails_classify_post_uses_path_and_force_true():
    handler = _HandlerStub()

    result = handle_emails_classify_post(handler, "/api/emails/classify/mail-1")

    assert result == ({"status": "ok", "email_uuid": "mail-1", "user_id": "u-1", "force": True}, 200)
