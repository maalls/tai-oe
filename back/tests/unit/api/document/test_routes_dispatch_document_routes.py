from types import SimpleNamespace

from src.api.document.routes import dispatch_document_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_document_routes_non_delete_returns_false():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/document/extract-rfp")

    assert dispatch_document_routes(handler, "GET", parsed, {"inline": ["1"]}, handler.request_handlers) is False
    assert dispatch_document_routes(handler, "POST", parsed, {}, handler.request_handlers) is False


def test_dispatch_document_routes_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.document.routes.handle_document_delete", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/document/doc-1")

    handled = dispatch_document_routes(handler, "DELETE", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "doc-1")]
