from types import SimpleNamespace

from src.api.entity.routes import dispatch_entity_routes


def test_dispatch_entity_routes_post_update(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append((handler, match.group(1), match.group(2)))

    monkeypatch.setattr("src.api.entity.routes.handle_entity_update_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/entity/opportunities/name")

    handled = dispatch_entity_routes(handler, "POST", parsed, {}, object())

    assert handled is True
    assert calls == [(handler, "opportunities", "name")]


def test_dispatch_entity_routes_non_post_returns_false():
    handler = object()
    parsed = SimpleNamespace(path="/api/entity/opportunities/name")

    handled = dispatch_entity_routes(handler, "GET", parsed, {}, object())

    assert handled is False
