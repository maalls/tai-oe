from types import SimpleNamespace

from src.api.document.routes import dispatch_document_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_document_routes_get_download(monkeypatch):
    calls = []

    def _fake(handler, parsed_path, qs, request_handlers):
        calls.append((handler, parsed_path, qs, request_handlers))

    monkeypatch.setattr("src.api.document.routes.handle_documents_download_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/documents/download/doc-1.pdf")

    handled = dispatch_document_routes(handler, "GET", parsed, {"inline": ["1"]}, handler.request_handlers)

    assert handled is True
    assert calls == [(handler, "/api/documents/download/doc-1.pdf", {"inline": ["1"]}, handler.request_handlers)]


def test_dispatch_document_routes_post_extract_rfp(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.document.routes.handle_document_extract_rfp_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/document/extract-rfp")

    handled = dispatch_document_routes(handler, "POST", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == [handler]


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
