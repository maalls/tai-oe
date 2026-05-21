from src.infrastructure.clients.oauth.azure_client import get_azure_oauth_url
from src.infrastructure.clients.oauth.state import decode_oauth_state
from urllib.parse import parse_qs, urlparse


def test_get_azure_oauth_url_uses_azur_settings(monkeypatch):
    monkeypatch.setenv("AZUR_CLIENT_ID", "client-id")
    monkeypatch.setenv("AZUR_REDIRECT_URI", "http://localhost:8000/api/outlook/oauth/callback")
    monkeypatch.setenv("AZUR_TENANT_ID", "common")

    result = get_azure_oauth_url(redirect_url="http://localhost:7153/settings")

    assert result["status"] == "ok"
    assert "login.microsoftonline.com/common/oauth2/v2.0/authorize" in result["auth_url"]
    assert "client_id=client-id" in result["auth_url"]
    query = parse_qs(urlparse(result["auth_url"]).query)
    state_value = query["state"][0]
    assert decode_oauth_state(state_value)["redirect_url"] == "http://localhost:7153/settings"
