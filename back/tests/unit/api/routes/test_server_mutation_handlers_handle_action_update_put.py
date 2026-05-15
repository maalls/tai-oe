from src.api.routes.server_mutation_handlers import handle_action_update_put


class _RequestHandlersStub:
    def handle_update_action(self, action_id, data, user_id):
        return {"status": "ok", "action_id": action_id, "data": data, "user_id": user_id}


class _MatchStub:
    def __init__(self, value):
        self.value = value

    def group(self, index):
        assert index == 1
        return self.value


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.json_calls = []

    def _read_json_or_error(self):
        return {"title": "updated"}

    def _require_auth_user_id(self):
        return "u-1"

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        self.json_calls.append((payload, status))
        return payload, status


def test_handle_action_update_put_calls_update_action_with_auth_user():
    handler = _HandlerStub()

    result = handle_action_update_put(handler, _MatchStub("a-1"))

    assert result == (
        {"status": "ok", "action_id": "a-1", "data": {"title": "updated"}, "user_id": "u-1"},
        200,
    )
