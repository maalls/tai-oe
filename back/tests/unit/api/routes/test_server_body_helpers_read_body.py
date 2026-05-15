from src.api.routes.server_body_helpers import read_body


class _ReaderStub:
    def __init__(self, payload):
        self.payload = payload
        self.last_size = None

    def read(self, size):
        self.last_size = size
        return self.payload


class _HandlerStub:
    def __init__(self):
        self.headers = {"Content-Length": "4"}
        self.rfile = _ReaderStub(b"test")


def test_read_body_reads_declared_content_length():
    handler = _HandlerStub()

    result = read_body(handler)

    assert result == b"test"
    assert handler.rfile.last_size == 4
