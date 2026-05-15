from src.api.routes.server_delete_handlers import handle_action_delete


class _RequestHandlersStub:
    def handle_delete_action(self, action_id, user_id):
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

    def _require_auth_user_id(self):
        return "u-1"

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_action_delete_uses_match_and_auth_user_id():
    handler = _HandlerStub()

    result = handle_action_delete(handler, _MatchStub("a-2"))

    assert result == ({"status": "ok", "action_id": "a-2", "user_id": "u-1"}, 200)
