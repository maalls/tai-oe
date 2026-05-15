from src.api.routes.server_auth_helpers import require_auth


class _AuthHandlerStub:
    def __init__(self, is_valid, user_data):
        self.is_valid = is_valid
        self.user_data = user_data

    def verify_token(self, auth_header):
        _ = auth_header
        return self.is_valid, self.user_data


class _HandlerStub:
    def __init__(self, auth_handler):
        self.headers = {"Authorization": "Bearer token"}
        self.auth_handler = auth_handler
        self.json_calls = []

    def get_auth_handler(self):
        return self.auth_handler

    def json(self, payload, status_code=200):
        self.json_calls.append((payload, status_code))
        return payload, status_code


def test_require_auth_returns_user_data_when_token_valid():
    handler = _HandlerStub(_AuthHandlerStub(True, {"id": "u-1"}))

    result = require_auth(handler)

    assert result == {"id": "u-1"}


def test_require_auth_emits_401_when_required_and_invalid():
    handler = _HandlerStub(_AuthHandlerStub(False, None))

    result = require_auth(handler, required=True)

    assert result is None
    assert handler.json_calls == [({"error_code": "UNAUTHORIZED", "message": "Unauthorized"}, 401)]
