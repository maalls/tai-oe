"""Unit tests for RequestHandlers fs/curl utility delegation during migration."""

from pathlib import Path

from src.controller.handlers import RequestHandlers


class _ResponseStub:
    def __init__(self, body: bytes, content_type: str = "application/json", status: int = 200):
        self._body = body
        self.headers = {"Content-Type": content_type}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


def test_handle_curl_request_uses_urlopen_and_formats_response(monkeypatch):
    calls = []

    def _urlopen(req, timeout):
        calls.append((req, timeout))
        return _ResponseStub(b'{"ok":true}', content_type="application/json", status=200)

    monkeypatch.setattr("src.controller.handlers.urllib.request.urlopen", _urlopen)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_curl_request(
        target_url="https://example.com/api",
        method="POST",
        headers={"Content-Type": "application/json"},
        body_text='{"x":1}',
        max_chars=50,
        timeout_ms=9000,
    )

    assert result["status"] == 200
    assert result["ok"] is True
    assert result["url"] == "https://example.com/api"
    assert result["content_type"] == "application/json"
    assert result["text"] == '{"ok":true}'
    assert len(calls) == 1
    req, timeout = calls[0]
    assert req.full_url == "https://example.com/api"
    assert req.get_method() == "POST"
    assert timeout == 9.0


def test_handle_fs_create_file_and_read(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    file_path = tmp_path / "a" / "b" / "c.txt"

    create_result = handlers.handle_fs_create(target_path=file_path, kind="file")
    assert create_result["status"] == "ok"
    assert create_result["type"] == "file"
    assert file_path.exists() and file_path.is_file()

    file_path.write_text("hello world", encoding="utf-8")
    read_result = handlers.handle_fs_read(target_path=file_path, max_chars=5)
    assert read_result["status"] == "ok"
    assert read_result["truncated"] is True
    assert read_result["text"] == "hello"


def test_handle_fs_create_dir(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    dir_path = tmp_path / "new-dir"

    create_result = handlers.handle_fs_create(target_path=dir_path, kind="dir")

    assert create_result == {
        "status": "ok",
        "path": str(dir_path),
        "type": "dir",
    }
    assert dir_path.exists() and dir_path.is_dir()


def test_handle_storage_find_path_prefers_known_subdirs(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    storage_dir = tmp_path / "storage"
    (storage_dir / "quotes").mkdir(parents=True, exist_ok=True)
    target = storage_dir / "quotes" / "quote_1.pdf"
    target.write_bytes(b"pdf")

    result = handlers.handle_storage_find_path(storage_dir, "quote_1.pdf")

    assert result == target


def test_handle_storage_file_metadata_pdf_inline(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    file_path = tmp_path / "quote_1.pdf"
    file_path.write_bytes(b"abcdef")

    metadata = handlers.handle_storage_file_metadata("quote_1.pdf", file_path)

    assert metadata["content_type"] == "application/pdf"
    assert metadata["file_size"] == 6
    assert metadata["content_disposition"].startswith("inline;")


def test_handle_storage_sanitize_filename_decodes_and_strips_traversal():
    handlers = RequestHandlers.__new__(RequestHandlers)

    sanitized = handlers.handle_storage_sanitize_filename("..%2Fsecret%2Fquote%201.pdf")

    assert sanitized == "secretquote 1.pdf"


def test_handle_storage_resolve_file_returns_path_and_metadata(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    storage_dir = tmp_path / "storage"
    (storage_dir / "quotes").mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / "quotes" / "quote_2.pdf"
    file_path.write_bytes(b"12345")

    result = handlers.handle_storage_resolve_file(storage_dir, "quote_2.pdf")

    assert result["filename"] == "quote_2.pdf"
    assert result["storage_path"] == file_path
    assert result["metadata"]["content_type"] == "application/pdf"
    assert result["metadata"]["file_size"] == 5


def test_handle_storage_resolve_file_raises_for_missing_file(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    storage_dir = tmp_path / "storage"

    try:
        handlers.handle_storage_resolve_file(storage_dir, "missing.pdf")
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError as exc:
        assert str(exc) == "Storage file not found: missing.pdf"


def test_handle_storage_read_chunks_streams_binary_content(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    file_path = tmp_path / "chunked.bin"
    file_path.write_bytes(b"abcdefghij")

    chunks = list(handlers.handle_storage_read_chunks(file_path, chunk_size=4))

    assert chunks == [b"abcd", b"efgh", b"ij"]


def test_handle_storage_response_headers_maps_metadata_to_http_headers():
    handlers = RequestHandlers.__new__(RequestHandlers)
    metadata = {
        "content_type": "application/pdf",
        "file_size": 123,
        "content_disposition": "inline; filename*=UTF-8''a.pdf",
    }

    headers = handlers.handle_storage_response_headers(metadata)

    assert headers == {
        "Content-Type": "application/pdf",
        "Content-Length": "123",
        "Accept-Ranges": "bytes",
        "Content-Disposition": "inline; filename*=UTF-8''a.pdf",
    }


def test_handle_storage_not_found_payload_for_head_response():
    handlers = RequestHandlers.__new__(RequestHandlers)

    payload = handlers.handle_storage_not_found_payload("..%2Fsecret%2Fa.pdf")

    assert payload == {
        "filename": "secreta.pdf",
        "content_type": "text/plain",
    }


def test_handle_storage_not_found_payload_for_get_response():
    handlers = RequestHandlers.__new__(RequestHandlers)

    payload = handlers.handle_storage_not_found_payload("missing.pdf", include_body=True)

    assert payload == {
        "filename": "missing.pdf",
        "content_type": "text/plain",
        "body": b"File not found",
    }


def test_handle_storage_read_error_payload_builds_500_text_response():
    handlers = RequestHandlers.__new__(RequestHandlers)

    payload = handlers.handle_storage_read_error_payload(RuntimeError("disk issue"))

    assert payload == {
        "content_type": "text/plain",
        "body": b"Error reading file: disk issue",
        "message": "Error reading file: disk issue",
    }
