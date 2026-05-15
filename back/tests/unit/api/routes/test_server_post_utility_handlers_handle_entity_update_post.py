from src.api.routes.server_post_utility_handlers import handle_entity_update_post


class _RequestHandlersStub:
    def handle_update_entity_field(self, **kwargs):
        return {"status": "ok", "kwargs": kwargs}


class _MatchStub:
    def group(self, index):
        if index == 1:
            return "contacts"
        if index == 2:
            return "name"
        raise AssertionError("unexpected index")


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def _read_json(self, default=None):
        _ = default
        return {"id": "c-1", "value": "Alice"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_entity_update_post_delegates_with_required_fields():
    handler = _HandlerStub()

    result = handle_entity_update_post(handler, _MatchStub())

    payload, status = result
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["kwargs"]["table"] == "contacts"
    assert payload["kwargs"]["field"] == "name"
    assert payload["kwargs"]["record_id"] == "c-1"
    assert payload["kwargs"]["value"] == "Alice"
    assert payload["kwargs"]["user_id"] == "u-1"
