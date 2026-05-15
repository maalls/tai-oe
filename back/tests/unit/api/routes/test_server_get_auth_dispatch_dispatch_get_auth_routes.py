from types import SimpleNamespace

from src.api.routes.server_get_auth_dispatch import dispatch_get_auth_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_auth_user_get(self):
        self.calls.append("auth_user")

    def _handle_oauth_login_get(self, qs):
        self.calls.append(("oauth_login", qs))


def test_dispatch_get_auth_routes_auth_user_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/auth/user")

    handled = dispatch_get_auth_routes(handler, parsed, {})

    assert handled is True
    assert handler.calls == ["auth_user"]


def test_dispatch_get_auth_routes_oauth_login_path():
    handler = _HandlerStub()
    parsed = SimpleNamespace(path="/api/oauth/login")

    handled = dispatch_get_auth_routes(handler, parsed, {"provider": ["azure"]})

    assert handled is True
    assert handler.calls == [("oauth_login", {"provider": ["azure"]})]
