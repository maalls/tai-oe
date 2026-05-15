from types import SimpleNamespace

from src.api.auth.routes import dispatch_auth_routes


def test_dispatch_auth_routes_get_auth_user(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(("auth_user", handler))

    monkeypatch.setattr("src.api.auth.routes.handle_auth_user_get", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/auth/user")

    handled = dispatch_auth_routes(handler, "GET", parsed, {})

    assert handled is True
    assert len(calls) == 1


def test_dispatch_auth_routes_post_login(monkeypatch):
    calls = []

    def _fake(handler):
        calls.append(("auth_login", handler))

    monkeypatch.setattr("src.api.auth.routes.handle_auth_login_post", _fake)

    handler = object()
    parsed = SimpleNamespace(path="/api/auth/login")

    handled = dispatch_auth_routes(handler, "POST", parsed, {})

    assert handled is True
    assert len(calls) == 1


def test_dispatch_auth_routes_unknown_path_returns_false():
    handler = object()
    parsed = SimpleNamespace(path="/api/auth/unknown")

    handled = dispatch_auth_routes(handler, "GET", parsed, {})

    assert handled is False
