"""Unit tests for RequestHandlers CSV upload delegation during migration."""

from src.api.router import RequestHandlers


class _FileHandlerStub:
    def __init__(self):
        self.calls = []

    def handle_file_upload(self, content_type: str, content_length: int, body: bytes):
        self.calls.append((content_type, content_length, body))
        return {"status": "ok", "stored": True}


def test_handle_csv_source_upload_uses_file_handler():
    handlers = RequestHandlers.__new__(RequestHandlers)
    handlers.file_handler = _FileHandlerStub()

    result = handlers.handle_csv_source_upload("multipart/form-data", 4, b"test")

    assert result == {"status": "ok", "stored": True}
    assert handlers.file_handler.calls == [("multipart/form-data", 4, b"test")]
