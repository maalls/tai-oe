import pytest

from src.api.routes.server_auth_helpers import authorize_request


class _AuthHandlerStub:
    def __init__(self, user_data):
        self.user_data = user_data

    def verify_token(self, _auth_header):
        return self.user_data is not None, self.user_data


class _HandlerStub:
    def __init__(self, user_data):
        self.headers = {"Authorization": "Bearer token"}
        self.auth_handler = _AuthHandlerStub(user_data)
        self.json_calls = []

    def json(self, payload, status_code=200):
        self.json_calls.append((payload, status_code))
        return payload, status_code


def test_authorize_request_returns_user_data_when_present():
    handler = _HandlerStub({"id": "u-1"})

    result = authorize_request(handler)

    assert result == {"id": "u-1"}


def test_authorize_request_raises_when_missing_user_data():
    handler = _HandlerStub(None)

    with pytest.raises(Exception):
        authorize_request(handler)
