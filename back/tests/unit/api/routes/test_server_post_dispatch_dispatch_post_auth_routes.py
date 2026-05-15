from src.api.routes.server_post_dispatch import dispatch_post_auth_routes
from src.api.routes import server_post_dispatch


class _HandlerStub:
    pass


def test_dispatch_post_auth_routes_login(monkeypatch):
    handler = _HandlerStub()
    seen = {}

    def _fake_dispatch_auth_routes(h, method, parsed, qs):
        seen["handler"] = h
        seen["method"] = method
        seen["path"] = parsed.path
        seen["qs"] = qs
        return True

    monkeypatch.setattr(server_post_dispatch, "dispatch_auth_routes", _fake_dispatch_auth_routes)

    handled = dispatch_post_auth_routes(handler, "/api/auth/login")

    assert handled is True
    assert seen == {
        "handler": handler,
        "method": "POST",
        "path": "/api/auth/login",
        "qs": {},
    }


def test_dispatch_post_auth_routes_unknown_path(monkeypatch):
    handler = _HandlerStub()

    monkeypatch.setattr(server_post_dispatch, "dispatch_auth_routes", lambda h, m, p, q: False)

    handled = dispatch_post_auth_routes(handler, "/api/auth/unknown")

    assert handled is False
