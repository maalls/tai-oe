"""Unit tests for RequestHandlers auth delegation during migration."""

from src.api.router import RequestHandlers


class _AuthHandlerStub:
    def __init__(self):
        self.calls = []

    def handle_signup(self, body: bytes):
        self.calls.append(("signup", body))
        return {"status": 201, "ok": True}

    def handle_login(self, body: bytes):
        self.calls.append(("login", body))
        return {"status": 200, "token": "t"}

    def handle_logout(self, auth_header: str):
        self.calls.append(("logout", auth_header))
        return {"status": 200, "ok": True}

    def handle_get_user(self, auth_header: str):
        self.calls.append(("user", auth_header))
        return {"status": 200, "user": {"id": "u-1"}}


def test_handle_auth_signup_uses_auth_handler(monkeypatch):
    stub = _AuthHandlerStub()
    monkeypatch.setattr("src.api.router.AuthHandler", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_auth_signup(b"{}")

    assert result == {"status": 201, "ok": True}
    assert stub.calls == [("signup", b"{}")]


def test_handle_auth_login_uses_auth_handler(monkeypatch):
    stub = _AuthHandlerStub()
    monkeypatch.setattr("src.api.router.AuthHandler", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_auth_login(b"{}")

    assert result == {"status": 200, "token": "t"}
    assert stub.calls == [("login", b"{}")]


def test_handle_auth_logout_uses_auth_handler(monkeypatch):
    stub = _AuthHandlerStub()
    monkeypatch.setattr("src.api.router.AuthHandler", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_auth_logout("Bearer abc")

    assert result == {"status": 200, "ok": True}
    assert stub.calls == [("logout", "Bearer abc")]


def test_handle_auth_user_uses_auth_handler(monkeypatch):
    stub = _AuthHandlerStub()
    monkeypatch.setattr("src.api.router.AuthHandler", lambda: stub)

    handlers = RequestHandlers.__new__(RequestHandlers)
    result = handlers.handle_auth_user("Bearer abc")

    assert result == {"status": 200, "user": {"id": "u-1"}}
    assert stub.calls == [("user", "Bearer abc")]
