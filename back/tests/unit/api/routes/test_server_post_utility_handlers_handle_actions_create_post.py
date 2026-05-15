from src.api.routes.server_post_utility_handlers import handle_actions_create_post


class _RequestHandlersStub:
    def handle_create_action(self, data, user_id):
        return {"status": "ok", "data": data, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _read_json_or_error(self):
        return {"kind": "email"}

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_actions_create_post_forwards_data_and_user_id():
    handler = _HandlerStub()

    result = handle_actions_create_post(handler)

    assert result == ({"status": "ok", "data": {"kind": "email"}, "user_id": "u-1"}, 200)
