from src.api.routes.dispatchers.server_delete_dispatch import dispatch_delete_request


class _HandlerStub:
    request_handlers = object()


def test_dispatch_delete_request_delegates_quote_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.routes.dispatchers.server_delete_dispatch.handle_quote_delete", _fake)

    handler = _HandlerStub()

    handled = dispatch_delete_request(handler, "/api/quote/q-1")

    assert handled is True
    assert calls == [(handler, "q-1")]


def test_dispatch_delete_request_delegates_opportunity_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.routes.dispatchers.server_delete_dispatch.handle_opportunity_delete", _fake)

    handler = _HandlerStub()

    handled = dispatch_delete_request(handler, "/api/opportunities/opp-1,opp-2")

    assert handled is True
    assert calls == [(handler, "opp-1,opp-2")]


def test_dispatch_delete_request_delegates_document_delete(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1)))

    monkeypatch.setattr("src.api.routes.dispatchers.server_delete_dispatch.handle_document_delete", _fake)

    handler = _HandlerStub()

    handled = dispatch_delete_request(handler, "/api/document/doc-1")

    assert handled is True
    assert calls == [(handler, "doc-1")]


def test_dispatch_delete_request_returns_false_when_unmatched(monkeypatch):
    handler = _HandlerStub()

    handled = dispatch_delete_request(handler, "/api/unknown")

    assert handled is False
