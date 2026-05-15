from src.api.routes.server_post_utility_handlers import handle_opportunities_create_manual_post


class _RequestHandlersStub:
    def handle_create_opportunity_manual(self, user_id, name):
        return {"status": "ok", "name": name, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def _read_json(self, default=None):
        _ = default
        return {"name": "Opportunity A"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_opportunities_create_manual_post_uses_name_and_user_id():
    handler = _HandlerStub()

    result = handle_opportunities_create_manual_post(handler)

    assert result == ({"status": "ok", "name": "Opportunity A", "user_id": "u-1"}, 200)
