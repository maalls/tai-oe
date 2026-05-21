from src.infrastructure.clients.outlook_client import OutlookClient


class _ResponseMock:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_outlook_client_get_profile_returns_me_payload(monkeypatch):
    def _fake_get(url, headers, timeout):
        assert url == "https://graph.microsoft.com/v1.0/me"
        assert headers["Authorization"] == "Bearer token-123"
        assert timeout == 15
        return _ResponseMock({"displayName": "John Doe", "mail": "john@example.com"})

    monkeypatch.setattr("src.infrastructure.clients.outlook_client.requests.get", _fake_get)

    client = OutlookClient(
        access_token="token-123",
        refresh_token="refresh-123",
        expires_at=9999999999,
        client_id="cid",
        client_secret="secret",
        tenant="common",
    )

    profile = client.get_profile()

    assert profile["displayName"] == "John Doe"
    assert profile["mail"] == "john@example.com"
