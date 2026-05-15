from types import SimpleNamespace

from src.api.action.routes import dispatch_action_routes


class _HandlerStub:
    request_handlers = object()


def test_dispatch_action_routes_get_action(monkeypatch):
    calls = []

    def _fake(handler, match, request_handlers):
        calls.append((match.group(1), request_handlers))

    monkeypatch.setattr("src.api.action.routes.handle_action_get", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-1")
    request_handlers = object()

    handled = dispatch_action_routes(handler, "GET", parsed, {}, request_handlers)

    assert handled is True
    assert calls == [("a-1", request_handlers)]


def test_dispatch_action_routes_post_execute(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append(match.group(1))

    monkeypatch.setattr("src.api.action.routes.handle_action_execute_post", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-2/execute")

    handled = dispatch_action_routes(handler, "POST", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == ["a-2"]


def test_dispatch_action_routes_delete_action(monkeypatch):
    calls = []

    def _fake(handler, match):
        calls.append(match.group(1))

    monkeypatch.setattr("src.api.action.routes.handle_action_delete", _fake)

    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-3")

    handled = dispatch_action_routes(handler, "DELETE", parsed, {}, handler.request_handlers)

    assert handled is True
    assert calls == ["a-3"]
