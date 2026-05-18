from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_data_routes


def test_dispatch_get_data_routes_csv_prefix_path():
    from src.api.routes.dispatchers import server_get_dispatch as module
    module.dispatch_csv_routes = lambda *_args, **_kwargs: True

    handler = object()
    parsed = SimpleNamespace(path="/api/csv/query")

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["x"]}, request_handlers=object())

    assert handled is True


def test_dispatch_get_data_routes_opportunity_path(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_get_dispatch.dispatch_opportunity_routes", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/opportunities/search")
    request_handlers = object()

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["acme"]}, request_handlers=request_handlers)

    assert handled is True
    assert calls == [(handler, "GET", "/api/opportunities/search", {"q": ["acme"]}, request_handlers)]


def test_dispatch_get_data_routes_delegates_opportunity_router(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.dispatchers.server_get_dispatch.dispatch_opportunity_routes", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/opportunities/search")
    request_handlers = object()

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["acme"]}, request_handlers=request_handlers)

    assert handled is True
    assert calls == [(handler, "GET", "/api/opportunities/search", {"q": ["acme"]}, request_handlers)]
