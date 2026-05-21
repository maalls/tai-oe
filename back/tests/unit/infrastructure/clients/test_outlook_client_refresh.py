import time

from src.infrastructure.clients.outlook_client import OutlookClient


class _ResponseMock:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_outlook_client_refresh_updates_tokens_and_calls_saver(monkeypatch):
    saved = {}

    def _fake_post(url, data, timeout):
        assert "oauth2/v2.0/token" in url
        assert data["grant_type"] == "refresh_token"
        assert timeout == 15
        return _ResponseMock(
            {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "Mail.Read Mail.Send offline_access",
            }
        )

    monkeypatch.setattr("src.infrastructure.clients.outlook_client.requests.post", _fake_post)

    def _save(tokens):
        saved.update(tokens)

    client = OutlookClient(
        access_token="old-access",
        refresh_token="old-refresh",
        expires_at=int(time.time()) - 10,
        client_id="cid",
        client_secret="secret",
        tenant="common",
        token_saver=_save,
    )

    client._refresh_if_needed()

    assert client.access_token == "new-access"
    assert client.refresh_token == "new-refresh"
    assert client.expires_at > int(time.time())
    assert saved["access_token"] == "new-access"
    assert saved["refresh_token"] == "new-refresh"
