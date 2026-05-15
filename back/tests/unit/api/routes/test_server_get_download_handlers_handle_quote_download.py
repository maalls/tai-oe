from src.api.routes.server_get_download_handlers import handle_quote_download


class _RequestHandlersStub:
    def handle_get_quote_file(self, filename):
        _ = filename
        return b"%PDF-1.4"


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
        self._cors_header_sent = False

    def send_response(self, code):
        self.response_code = code

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        self.ended = True

    def _send_error(self, code, message):
        self.errors.append((code, message))
        return code, message


def test_handle_quote_download_streams_pdf_inline_when_requested():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub()

    result = handle_quote_download(
        handler,
        "quote.pdf",
        request_handlers,
        {"inline": ["1"]},
    )

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "application/pdf"
    assert handler.sent_headers["Content-Disposition"] == 'inline; filename="quote.pdf"'
    assert handler.wfile.chunks == [b"%PDF-1.4"]
    assert handler._cors_header_sent is True


def test_handle_quote_download_returns_not_found():
    handler = _HandlerStub()

    class _NotFoundRequestHandlersStub:
        def handle_get_quote_file(self, filename):
            _ = filename
            raise FileNotFoundError()

    result = handle_quote_download(handler, "missing.pdf", _NotFoundRequestHandlersStub())

    assert result == (404, "Quote file not found")
