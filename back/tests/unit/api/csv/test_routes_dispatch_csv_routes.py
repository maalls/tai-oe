from types import SimpleNamespace

from src.api.csv.routes import dispatch_csv_routes


def test_dispatch_csv_routes_get_prefix(monkeypatch):
    calls = []

    def _fake(handler, parsed_path, qs):
        calls.append((parsed_path, qs))

    monkeypatch.setattr("src.api.csv.routes.handle_csv_get", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/csv/query")

    handled = dispatch_csv_routes(handler, "GET", parsed, {"q": ["abc"]})

    assert handled is True
    assert calls == [("/api/csv/query", {"q": ["abc"]})]


def test_dispatch_csv_routes_post_source(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(handler)

    monkeypatch.setattr("src.api.csv.routes.handle_csv_source_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/csv/source")

    handled = dispatch_csv_routes(handler, "POST", parsed, {})

    assert handled is True
    assert len(calls) == 1


def test_dispatch_csv_routes_non_csv_get_returns_false():
    handler = object()
    parsed = SimpleNamespace(path="/api/quotes/list")

    handled = dispatch_csv_routes(handler, "GET", parsed, {})

    assert handled is False
