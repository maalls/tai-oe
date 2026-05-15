from src.api.routes.server_post_utility_handlers import handle_quote_submit_post


class _RequestHandlersStub:
    def handle_quote_submit(self, body, content_type):
        return {"status": "ok", "body": body, "content_type": content_type}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Content-Type": "application/json"}

    def _read_body(self):
        return b"{}"

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        return payload, status


def test_handle_quote_submit_post_reads_body_and_content_type():
    handler = _HandlerStub()

    result = handle_quote_submit_post(handler)

    assert result == ({"status": "ok", "body": b"{}", "content_type": "application/json"}, 200)
