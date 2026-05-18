from types import SimpleNamespace

from src.api.routes.dispatchers import server_get_dispatch


class _HandlerStub:
    def __init__(self):
        self.request_handlers = "rh"


def test_dispatch_get_request_calls_data_then_action_groups(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/actions/a-1")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_data_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_action_download_routes", lambda h, p, q, rh: rh == "rh")

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True


def test_dispatch_get_request_returns_false_when_nothing_matches(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/unknown")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_data_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_action_download_routes", lambda h, p, q, rh: False)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is False
