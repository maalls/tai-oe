from src.infrastructure.clients.oauth.azure_client import handle_azure_oauth_callback
from src.infrastructure.clients.oauth.state import encode_oauth_state


class _ResponseMock:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_handle_azure_oauth_callback_exchanges_code(monkeypatch):
    monkeypatch.setenv("AZUR_CLIENT_ID", "client-id")
    monkeypatch.setenv("AZUR_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("AZUR_REDIRECT_URI", "http://localhost:8000/api/outlook/oauth/callback")
    monkeypatch.setenv("AZUR_TENANT_ID", "common")

    captured = {}

    def _fake_post(url, data, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return _ResponseMock({"access_token": "token-123"})

    monkeypatch.setattr("src.infrastructure.clients.oauth.azure_client.requests.post", _fake_post)

    state = encode_oauth_state({"redirect_url": "http://localhost:7153/settings"})
    result = handle_azure_oauth_callback(code="code-abc", state=state)

    assert result["status"] == "ok"
    assert result["tokens"]["access_token"] == "token-123"
    assert result["redirect_url"] == "http://localhost:7153/settings"
    assert captured["timeout"] == 15
    assert "oauth2/v2.0/token" in captured["url"]
    assert captured["data"]["scope"] == "Mail.Read Mail.Send offline_access"
