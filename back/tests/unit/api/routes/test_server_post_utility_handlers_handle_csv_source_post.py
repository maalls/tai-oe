from src.api.routes.server_post_utility_handlers import handle_csv_source_post


class _RequestHandlersStub:
    def handle_csv_source_upload(self, content_type, content_length, body):
        return {
            "status": "ok",
            "content_type": content_type,
            "content_length": content_length,
            "body": body,
        }


class _HandlerStub:
    def __init__(self):
        self.request_handlers = _RequestHandlersStub()
        self.headers = {"Content-Type": "text/csv"}

    def _read_body(self):
        return b"a,b\n1,2\n"

    def get_request_handlers(self):
        return self.request_handlers

    def json(self, payload, status=200):
        return payload, status


def test_handle_csv_source_post_forwards_body_and_length():
    handler = _HandlerStub()

    result = handle_csv_source_post(handler)

    assert result == (
        {
            "status": "ok",
            "content_type": "text/csv",
            "content_length": 8,
            "body": b"a,b\n1,2\n",
        },
        200,
    )
