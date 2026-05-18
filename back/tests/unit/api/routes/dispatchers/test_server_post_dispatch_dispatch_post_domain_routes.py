from types import SimpleNamespace

from src.api.routes.dispatchers.server_post_dispatch import dispatch_post_domain_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []
        self.request_handlers = object()

    def _handle_entity_update_post(self, match):
        self.calls.append(("entity", match.group(1), match.group(2)))

def test_dispatch_post_domain_routes_entity_update_regex():
    calls = []

    def _entity_router(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    from src.api.routes.dispatchers import server_post_dispatch as module
    module.dispatch_entity_routes = _entity_router

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/entity/opportunities/name")

    handled = dispatch_post_domain_routes(handler, parsed)

    assert handled is True
    assert calls == [(handler, "POST", "/api/entity/opportunities/name", {}, handler.request_handlers)]


def test_dispatch_post_domain_routes_returns_false_for_legacy_email_path():
    from src.api.routes.dispatchers import server_post_dispatch as module
    module.dispatch_entity_routes = lambda *_args, **_kwargs: False

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/emails/classify/abc")

    handled = dispatch_post_domain_routes(handler, parsed)

    assert handled is False


def test_dispatch_post_domain_routes_returns_false_when_not_handled(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_post_dispatch.dispatch_entity_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/opportunity/opp-1/send-quote")

    handled = dispatch_post_domain_routes(handler, parsed)

    assert handled is False
