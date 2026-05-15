from src.api.routes.server_get_stream_handlers import handle_source_stream


class _RequestHandlersStub:
    def handle_source_raw(self, qs):
        _ = qs
        return b"excel-binary"


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


def test_handle_source_stream_sends_attachment_headers():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub()

    result = handle_source_stream(handler, {"source": ["sales.xlsx"]}, request_handlers)

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert handler.sent_headers["Content-Disposition"] == 'attachment; filename="sales.xlsx"'
    assert handler.wfile.chunks == [b"excel-binary"]


def test_handle_source_stream_requires_source_parameter():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub()

    result = handle_source_stream(handler, {}, request_handlers)

    assert result == (400, "Missing 'source' parameter")
