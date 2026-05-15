from src.api.routes.server_delete_handlers import handle_imap_config_delete


class _RequestHandlersStub:
    def handle_imap_config_delete(self, user_id):
        return {"status": "ok", "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def _require_auth_user_id(self):
        return "u-1"

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_imap_config_delete_calls_service_with_user_id():
    handler = _HandlerStub()

    result = handle_imap_config_delete(handler)

    assert result == ({"status": "ok", "user_id": "u-1"}, 200)
