from src.api.routes.server_post_legacy_dispatch import (
    dispatch_action_post_routes,
    dispatch_post_legacy_and_action_routes,
)


class _HandlerStub:
    request_handlers = object()


def test_dispatch_post_legacy_and_action_routes_csv_source(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.server_post_legacy_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: True,
    )

    handler = _HandlerStub()

    handled = dispatch_post_legacy_and_action_routes(handler, "/api/csv/source")

    assert handled is True


def test_dispatch_post_legacy_and_action_routes_delegates_rfq_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.server_post_legacy_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_post_legacy_dispatch.dispatch_rfq_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_post_legacy_and_action_routes(handler, "/api/rfp")

    assert handled is True
    assert calls == [(handler, "POST", "/api/rfp", {}, handler.request_handlers)]


def test_dispatch_action_post_routes_pause_regex(monkeypatch):
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_post_legacy_dispatch.dispatch_action_routes", _fake)

    handler = _HandlerStub()

    handled = dispatch_action_post_routes(handler, "/api/actions/a-1/pause")

    assert handled is True
    assert calls == [(handler, "POST", "/api/actions/a-1/pause", {}, handler.request_handlers)]
