from src.api.routes.dispatchers.server_post_dispatch import (
    dispatch_action_post_routes,
    dispatch_post_legacy_and_action_routes,
)


class _HandlerStub:
    request_handlers = object()


def test_dispatch_post_legacy_and_action_routes_delegates_action_routes(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_post_dispatch.dispatch_action_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_post_legacy_and_action_routes(handler, "/api/actions/a-1/pause")

    assert handled is True
    assert calls == [(handler, "POST", "/api/actions/a-1/pause", {}, handler.request_handlers)]


def test_dispatch_post_legacy_and_action_routes_returns_false_when_unhandled(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_post_dispatch.dispatch_action_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = _HandlerStub()

    handled = dispatch_post_legacy_and_action_routes(handler, "/api/unhandled")

    assert handled is False


def test_dispatch_action_post_routes_pause_regex(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_post_dispatch.dispatch_action_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_action_post_routes(handler, "/api/actions/a-1/pause")

    assert handled is True
    assert calls == [(handler, "POST", "/api/actions/a-1/pause", {}, handler.request_handlers)]
