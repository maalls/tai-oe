"""Unit tests for RequestHandlers utility delegation during migration."""

from src.api.router import RequestHandlers


class _ResponseStub:
    def __init__(self, body: bytes, content_type: str = "text/plain", status: int = 200):
        self._body = body
        self.headers = {"Content-Type": content_type}
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


def test_handle_fetch_url_uses_urlopen_and_formats_response(monkeypatch):
    calls = []

    def _urlopen(url, timeout):
        calls.append((url, timeout))
        return _ResponseStub(b"hello world", content_type="text/plain", status=200)

    monkeypatch.setattr("src.api.router.urllib.request.urlopen", _urlopen)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_fetch_url("https://example.com", max_chars=5, timeout_ms=8000)

    assert result == {
        "status": 200,
        "ok": True,
        "url": "https://example.com",
        "content_type": "text/plain",
        "truncated": True,
        "text": "hello",
    }
    assert calls == [("https://example.com", 8.0)]
