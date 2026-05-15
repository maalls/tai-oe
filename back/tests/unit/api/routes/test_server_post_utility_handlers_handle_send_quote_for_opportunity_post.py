from src.api.routes.server_post_utility_handlers import handle_send_quote_for_opportunity_post


class _MatchStub:
    def group(self, idx):
        assert idx == 1
        return "opp-1"


class _RequestHandlersStub:
    def handle_send_quote_for_opportunity(self, opportunity_id, payload, user_id):
        return {"status": "ok", "opportunity_id": opportunity_id, "payload": payload, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def _read_json_or_error(self):
        return {"to": "x@example.com"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200 if result.get("status") == "ok" else 400

    def json(self, payload, status=200):
        return payload, status


def test_handle_send_quote_for_opportunity_post_forwards_match_payload_and_user():
    handler = _HandlerStub()

    result = handle_send_quote_for_opportunity_post(handler, _MatchStub())

    assert result == (
        {
            "status": "ok",
            "opportunity_id": "opp-1",
            "payload": {"to": "x@example.com"},
            "user_id": "u-1",
        },
        200,
    )
