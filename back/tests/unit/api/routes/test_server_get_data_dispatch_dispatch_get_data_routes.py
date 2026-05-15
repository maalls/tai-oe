from types import SimpleNamespace

from src.api.routes.server_get_data_dispatch import dispatch_get_data_routes


def test_dispatch_get_data_routes_csv_prefix_path():
    from src.api.routes import server_get_data_dispatch as module
    module.dispatch_csv_routes = lambda *_args, **_kwargs: True

    handler = object()
    parsed = SimpleNamespace(path="/api/csv/query")

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["x"]}, request_handlers=object())

    assert handled is True


def test_dispatch_get_data_routes_quotes_list_path(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.server_get_data_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: False,
    )
    calls = []

    def _fake(handler, method, parsed, qs, request_handlers):
        calls.append((handler, method, parsed.path, qs, request_handlers))
        return True

    monkeypatch.setattr("src.api.routes.server_get_data_dispatch.dispatch_quote_routes", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/quotes/list")
    request_handlers = object()

    handled = dispatch_get_data_routes(handler, parsed, {}, request_handlers=request_handlers)

    assert handled is True
    assert calls == [(handler, "GET", "/api/quotes/list", {}, request_handlers)]
