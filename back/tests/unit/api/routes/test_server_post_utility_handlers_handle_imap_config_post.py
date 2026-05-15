from src.api.routes.server_post_utility_handlers import handle_imap_config_post


class _RequestHandlersStub:
    def handle_imap_config_save(self, user_id, payload):
        return {"status": "ok", "user_id": user_id, "payload": payload}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json(self, default=None):
        return {"host": "imap.example.com", "port": 993}

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_imap_config_post_passes_user_id_and_payload():
    handler = _HandlerStub()

    result = handle_imap_config_post(handler)

    assert result == (
        {
            "status": "ok",
            "user_id": "u-1",
            "payload": {"host": "imap.example.com", "port": 993},
        },
        200,
    )
