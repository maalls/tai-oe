import pytest

from src.api.routes.server_auth_helpers import authorize_request


class _HandlerStub:
    def __init__(self, user_data):
        self.user_data = user_data

    def _require_auth(self):
        return self.user_data


def test_authorize_request_returns_user_data_when_present():
    handler = _HandlerStub({"id": "u-1"})

    result = authorize_request(handler)

    assert result == {"id": "u-1"}


def test_authorize_request_raises_when_missing_user_data():
    handler = _HandlerStub(None)

    with pytest.raises(Exception):
        authorize_request(handler)
