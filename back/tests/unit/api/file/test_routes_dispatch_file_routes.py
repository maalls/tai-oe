from types import SimpleNamespace

from src.api.file.routes import dispatch_file_routes


class _HandlerStub:
    config = {"STORAGE_DIR": "/tmp/storage"}


def test_dispatch_file_routes_get_fetch(monkeypatch):
    calls = []

    def _fake(handler, qs):
        calls.append((handler, qs))

    monkeypatch.setattr("src.api.file.routes.handle_fetch_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/fetch")

    handled = dispatch_file_routes(handler, "GET", parsed, {"source": ["a"]}, object())

    assert handled is True
    assert calls == [(handler, {"source": ["a"]})]


def test_dispatch_file_routes_head_storage(monkeypatch):
    calls = []

    def _fake(handler, storage_dir, parsed_path):
        calls.append((handler, storage_dir, parsed_path))

    monkeypatch.setattr("src.api.file.routes.handle_storage_head", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/storage/file.pdf")

    handled = dispatch_file_routes(handler, "HEAD", parsed, {}, object())

    assert handled is True
    assert calls == [(handler, "/tmp/storage", "/api/storage/file.pdf")]


def test_dispatch_file_routes_post_curl(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.file.routes.handle_curl_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/curl")

    handled = dispatch_file_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [handler]
