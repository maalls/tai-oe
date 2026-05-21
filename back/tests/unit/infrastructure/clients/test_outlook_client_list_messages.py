from src.infrastructure.clients.outlook_client import OutlookClient


class _ResponseMock:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_outlook_client_list_messages_returns_value_list(monkeypatch):
    def _fake_get(url, headers, timeout):
        assert "https://graph.microsoft.com/v1.0/me/messages" in url
        assert "$top=5" in url
        assert headers["Authorization"] == "Bearer token-123"
        assert timeout == 15
        return _ResponseMock({"value": [{"id": "m1"}, {"id": "m2"}]})

    monkeypatch.setattr("src.infrastructure.clients.outlook_client.requests.get", _fake_get)

    client = OutlookClient(
        access_token="token-123",
        refresh_token="refresh-123",
        expires_at=9999999999,
        client_id="cid",
        client_secret="secret",
        tenant="common",
    )

    messages = client.list_messages(max_results=5)

    assert len(messages) == 2
    assert messages[0]["id"] == "m1"
