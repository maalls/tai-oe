import requests

from src.infrastructure.clients.outlook_client import handle_outlook_oauth_callback


class _ResponseMock:
    def raise_for_status(self):
        raise requests.HTTPError(response=self)

    def json(self):
        return {"error_description": "AADSTS7000215: Invalid client secret"}


def test_handle_outlook_oauth_callback_surfaces_http_error_message(monkeypatch):
    def _fake_post(url, data, timeout):
        return _ResponseMock()

    monkeypatch.setenv("AZUR_CLIENT_ID", "client-id")
    monkeypatch.setenv("AZUR_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("AZUR_TENANT_ID", "common")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173/")
    monkeypatch.setattr("src.infrastructure.clients.outlook_client.requests.post", _fake_post)

    result = handle_outlook_oauth_callback(code="code-abc", state=None)

    assert result["status"] == "error"
    assert "Invalid client secret" in result["message"]
