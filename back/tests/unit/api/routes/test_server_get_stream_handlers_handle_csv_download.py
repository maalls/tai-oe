from src.api.routes.server_get_stream_handlers import handle_csv_download


class _FileHandlerStub:
    def __init__(self, path):
        self.path = path

    def safe_file_from_query(self, source, sheet):
        _ = source
        _ = sheet
        return self.path


class _RequestHandlersStub:
    def __init__(self, path):
        self.file_handler = _FileHandlerStub(path)


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


def test_handle_csv_download_streams_file_content(tmp_path):
    csv_path = tmp_path / "sheet.csv"
    csv_path.write_bytes(b"a,b\n1,2\n")

    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub(csv_path)

    result = handle_csv_download(
        handler,
        {"source": ["s.xlsx"], "file": ["sheet.csv"]},
        request_handlers,
    )

    assert result is None
    assert handler.response_code == 200
    assert handler.sent_headers["Content-Type"] == "text/csv; charset=utf-8"
    assert handler.sent_headers["Content-Disposition"] == 'attachment; filename="sheet.csv"'
    assert b"".join(handler.wfile.chunks) == b"a,b\n1,2\n"


def test_handle_csv_download_requires_source_and_file():
    handler = _HandlerStub()
    request_handlers = _RequestHandlersStub(path=None)

    result = handle_csv_download(handler, {"source": ["x"]}, request_handlers)

    assert result == (400, "Missing 'source' or 'file' parameter")
