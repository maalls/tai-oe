from src.api.routes.server_post_utility_handlers import handle_opportunity_rfq_generate_post


class _MatchStub:
    def group(self, idx):
        assert idx == 1
        return "opp-1"


class _RequestHandlersStub:
    def handle_generate_quote_for_opportunity(self, opportunity_id, user_id):
        return {"status": "ok", "opportunity_id": opportunity_id, "user_id": user_id}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_opportunity_rfq_generate_post_forwards_opportunity_and_user():
    handler = _HandlerStub()

    result = handle_opportunity_rfq_generate_post(handler, _MatchStub())

    assert result == ({"status": "ok", "opportunity_id": "opp-1", "user_id": "u-1"}, 200)
