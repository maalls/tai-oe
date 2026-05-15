from types import SimpleNamespace

from src.api.routes.dispatchers.server_get_dispatch import dispatch_get_auth_routes
from src.api.routes.dispatchers import server_get_dispatch


class _HandlerStub:
    pass


def test_dispatch_get_auth_routes_auth_user_path(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/auth/user")
    seen = {}

    def _fake_dispatch_auth_routes(h, method, p, qs):
        seen["handler"] = h
        seen["method"] = method
        seen["path"] = p.path
        seen["qs"] = qs
        return True

    monkeypatch.setattr(server_get_dispatch, "dispatch_auth_routes", _fake_dispatch_auth_routes)

    handled = dispatch_get_auth_routes(handler, parsed, {})

    assert handled is True
    assert seen == {
        "handler": handler,
        "method": "GET",
        "path": "/api/auth/user",
        "qs": {},
    }


def test_dispatch_get_auth_routes_oauth_login_path(monkeypatch):
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/oauth/login")

    monkeypatch.setattr(server_get_dispatch, "dispatch_auth_routes", lambda h, m, p, qs: True)

    handled = dispatch_get_auth_routes(handler, parsed, {"provider": ["azure"]})

    assert handled is True
