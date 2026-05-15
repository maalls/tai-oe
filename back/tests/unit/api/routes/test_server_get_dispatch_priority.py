from types import SimpleNamespace

from src.api.routes import server_get_dispatch


class _HandlerStub:
    def _handle_ddd_get_routes(self, parsed, qs):
        _ = (parsed, qs)
        return False


def test_dispatch_get_request_short_circuits_on_ddd(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/anything")

    monkeypatch.setattr(handler, "_handle_ddd_get_routes", lambda parsed, qs: True)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True


def test_dispatch_get_request_uses_auth_group(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/auth/user")

    monkeypatch.setattr(server_get_dispatch, "dispatch_get_misc_routes", lambda h, p, q: False)
    monkeypatch.setattr(server_get_dispatch, "dispatch_get_auth_routes", lambda h, p, q: True)

    handled = server_get_dispatch.dispatch_get_request(handler, parsed, {})

    assert handled is True
