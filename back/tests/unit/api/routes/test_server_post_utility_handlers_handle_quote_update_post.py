from src.api.routes.server_post_utility_handlers import handle_quote_update_post


class _MatchStub:
    def group(self, idx):
        assert idx == 1
        return "q-1"


class _RequestHandlersStub:
    def handle_update_quote(self, document_id, payload, user_id):
        return {"status": "ok", "document_id": document_id, "payload": payload, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def _read_json(self, default=None):
        return {"field": "value"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_error(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_quote_update_post_uses_status_from_error():
    handler = _HandlerStub()

    result = handle_quote_update_post(handler, _MatchStub())

    assert result == (
        {"status": "ok", "document_id": "q-1", "payload": {"field": "value"}, "user_id": "u-1"},
        200,
    )
