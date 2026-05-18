from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_data_routes


def test_dispatch_get_data_routes_csv_prefix_path():
    from src.api.routes.dispatchers import server_get_dispatch as module
    module.dispatch_csv_routes = lambda *_args, **_kwargs: True

    handler = object()
    parsed = SimpleNamespace(path="/api/csv/query")

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["x"]})

    assert handled is True


def test_dispatch_get_data_routes_returns_false_when_csv_not_handled(monkeypatch):
    monkeypatch.setattr(
        "src.api.routes.dispatchers.server_get_dispatch.dispatch_csv_routes",
        lambda *_args, **_kwargs: False,
    )

    handler = object()
    parsed = SimpleNamespace(path="/api/opportunities/search")

    handled = dispatch_get_data_routes(handler, parsed, {"q": ["acme"]})

    assert handled is False
