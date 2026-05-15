from src.api.routes.server_get_stream_handlers import handle_raw_stream


class _RequestHandlersStub:
    def handle_raw(self, qs):
        return b"a,b\n1,2\n"


class _Writer:
    def __init__(self):
        self.chunks = []

    def write(self, data):
        self.chunks.append(data)


class _HandlerStub:
    def __init__(self):
        self.response_code = None
        self.sent_headers = {}
        self.ended = False
        self.wfile = _Writer()
        self.errors = []

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        self.ended = True

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message


def test_handle_raw_stream_writes_csv_content():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub()

    result = handle_raw_stream(handler, {"file": ["x"]}, request_handlers)

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "text/csv; charset=utf-8"
    assert handler.wfile.chunks == [b"a,b\n1,2\n"]
