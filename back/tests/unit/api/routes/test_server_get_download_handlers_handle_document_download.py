from src.api.routes.server_get_download_handlers import handle_document_download


class _RequestHandlersStub:
    def handle_get_document_file(self, filename):
        _ = filename
        return b"doc-bytes"


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


def test_handle_document_download_streams_with_extension_content_type():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub()

    result = handle_document_download(
        handler,
        "spec.docx",
        request_handlers,
        {"inline": ["0"]},
    )

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert handler.sent_headers["Content-Disposition"] == 'attachment; filename="spec.docx"'
    assert handler.wfile.chunks == [b"doc-bytes"]
    assert handler._cors_header_sent is True


def test_handle_document_download_returns_not_found():
    handler = _HandlerStub()

    class _NotFoundRequestHandlersStub:
        def handle_get_document_file(self, filename):
            _ = filename
            raise FileNotFoundError()

    result = handle_document_download(handler, "missing.pdf", _NotFoundRequestHandlersStub())

    assert result == (404, "Document file not found")
