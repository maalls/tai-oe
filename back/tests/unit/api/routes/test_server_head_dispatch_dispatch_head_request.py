from src.api.routes.dispatchers.server_head_dispatch import dispatch_head_request


class _HandlerStub:
    request_handlers = object()


def test_dispatch_head_request_routes_storage_path(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_head_dispatch.dispatch_file_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/storage/example.pdf")

    assert handled is True
    assert calls == [(handler, "HEAD", "/api/storage/example.pdf", {}, handler.request_handlers)]


def test_dispatch_head_request_returns_false_for_unknown_path(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_head_dispatch.dispatch_file_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = _HandlerStub()

    handled = dispatch_head_request(handler, "/api/unknown")

    assert handled is False
