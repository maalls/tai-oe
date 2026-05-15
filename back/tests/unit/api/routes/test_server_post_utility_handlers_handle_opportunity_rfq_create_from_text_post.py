from src.api.routes.server_post_utility_handlers import handle_opportunity_rfq_create_from_text_post


class _MatchStub:
    def __init__(self, value):
        self.value = value

    def group(self, idx):
        assert idx == 1
        return self.value


class _RequestHandlersStub:
    def __init__(self):
        self.generated_for = None

    def handle_create_rfq_source_from_html_body(self, opportunity_id, body, content_type, user_id):
        return {
            "status": "ok",
            "opportunity_id": opportunity_id,
            "body": body,
            "content_type": content_type,
            "user_id": user_id,
        }

    def handle_create_opportunity_from_rfp(self, body, content_type, user_id):
        return {"status": "ok", "opportunity": {"id": "opp-new"}}

    def handle_generate_quote_for_opportunity(self, opportunity_id, user_id):
        self.generated_for = (opportunity_id, user_id)
        return {"status": "ok"}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Content-Type": "text/html"}

    def _read_body(self):
        return b"<html/>"

    def _require_auth(self):
        return {"id": "u-1"}

    def get_request_handlers(self):
        return self.request_handlers

    def _status_from_result(self, result):
        return 200

    def json(self, payload, status=200):
        return payload, status


def test_handle_opportunity_rfq_create_from_text_post_existing_opportunity_branch():
    handler = _HandlerStub()

    result = handle_opportunity_rfq_create_from_text_post(handler, _MatchStub("opp-1"))

    assert result == (
        {
            "status": "ok",
            "opportunity_id": "opp-1",
            "body": b"<html/>",
            "content_type": "text/html",
            "user_id": "u-1",
        },
        200,
    )


def test_handle_opportunity_rfq_create_from_text_post_new_branch_triggers_generate():
    handler = _HandlerStub()

    result = handle_opportunity_rfq_create_from_text_post(handler, _MatchStub("new"))

    assert result == ({"status": "ok", "opportunity": {"id": "opp-new"}}, 200)
    assert handler.request_handlers.generated_for == ("opp-new", "u-1")
