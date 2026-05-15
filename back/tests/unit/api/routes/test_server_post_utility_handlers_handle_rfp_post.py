from src.api.routes.server_post_utility_handlers import handle_rfp_post


class _RequestHandlersStub:
    def handle_rfp_upload(self, body, content_type):
        return {"status": "ok", "body": body, "content_type": content_type}


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Content-Type": "text/plain"}

    def _read_body(self):
        return b"rfp"

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        return payload, status


def test_handle_rfp_post_reads_body_and_content_type():
    handler = _HandlerStub()

    result = handle_rfp_post(handler)

    assert result == ({"status": "ok", "body": b"rfp", "content_type": "text/plain"}, 200)
