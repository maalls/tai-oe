from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_action_download_routes


class _HandlerStub:
    pass


def test_dispatch_get_action_download_routes_delegates_action_router(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_get_dispatch.dispatch_action_routes", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-42")
    request_handlers = object()

    handled = dispatch_get_action_download_routes(handler, parsed, {}, request_handlers=request_handlers)

    assert handled is True
    assert calls == [(handler, "GET", "/api/actions/a-42", {}, request_handlers)]


def test_dispatch_get_action_download_routes_delegates_quote_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_action_routes",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_document_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quotes/download/file.pdf")
    request_handlers = object()

    handled = dispatch_get_action_download_routes(handler, parsed, {"inline": ["1"]}, request_handlers=request_handlers)

    assert handled is False


def test_dispatch_get_action_download_routes_delegates_document_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_action_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_get_dispatch.dispatch_document_routes", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/documents/download/doc.pdf")
    request_handlers = object()

    handled = dispatch_get_action_download_routes(handler, parsed, {"inline": ["1"]}, request_handlers=request_handlers)

    assert handled is True
    assert calls == [(handler, "GET", "/api/documents/download/doc.pdf", {"inline": ["1"]}, request_handlers)]
