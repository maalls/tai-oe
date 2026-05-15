from types import SimpleNamespace

from src.api.routes.server_post_business_dispatch import dispatch_post_business_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []
        self.request_handlers = object()

    def _handle_send_quote_for_opportunity_post(self, match):
        self.calls.append(("send_quote", match.group(1)))

def test_dispatch_post_business_routes_send_quote_regex():
    calls = []

    def _opp_router(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    def _doc_router(*_args, **_kwargs):
        return False

    def _invoice_router(*_args, **_kwargs):
        return False

    def _quote_router(*_args, **_kwargs):
        return False

    from src.api.routes import server_post_business_dispatch as module
    module.dispatch_opportunity_routes = _opp_router
    module.dispatch_document_routes = _doc_router
    module.dispatch_quote_routes = _quote_router
    module.dispatch_invoice_routes = _invoice_router

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunity/opp-1/send-quote")

    handled = dispatch_post_business_routes(handler, parsed)

    assert handled is True
    assert calls == [(handler, "POST", "/api/opportunity/opp-1/send-quote", {}, handler.request_handlers)]


def test_dispatch_post_business_routes_delegates_quote_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.server_post_business_dispatch.dispatch_opportunity_routes",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        "src.api.routes.server_post_business_dispatch.dispatch_document_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _quote_router(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_post_business_dispatch.dispatch_quote_routes", _quote_router)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/quote/doc-8/pdf")

    handled = dispatch_post_business_routes(handler, parsed)

    assert handled is True
    assert calls == [(handler, "POST", "/api/quote/doc-8/pdf", {}, handler.request_handlers)]
