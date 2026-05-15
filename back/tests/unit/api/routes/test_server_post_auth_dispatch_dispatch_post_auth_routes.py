from src.api.routes.server_post_auth_dispatch import dispatch_post_auth_routes


class _HandlerStub:
    def __init__(self):
        self.calls = []

    def _handle_auth_signup_post(self):
        self.calls.append("signup")

    def _handle_auth_login_post(self):
        self.calls.append("login")

    def _handle_auth_logout_post(self):
        self.calls.append("logout")


def test_dispatch_post_auth_routes_login():
    handler = _HandlerStub()

    handled = dispatch_post_auth_routes(handler, "/api/auth/login")

    assert handled is True
    assert handler.calls == ["login"]


def test_dispatch_post_auth_routes_unknown_path():
    handler = _HandlerStub()

    handled = dispatch_post_auth_routes(handler, "/api/auth/unknown")

    assert handled is False
    assert handler.calls == []
