import requests

from src.infrastructure.clients.outlook_client import OutlookClient


class _ResponseMock:
    def raise_for_status(self):
        raise requests.HTTPError(response=self)

    def json(self):
        return {"error_description": "Missing User.Read scope"}


def test_outlook_client_get_profile_surfaces_graph_error_message(monkeypatch):
    def _fake_get(url, headers, timeout):
        return _ResponseMock()

    monkeypatch.setattr("src.infrastructure.clients.outlook_client.requests.get", _fake_get)

    client = OutlookClient(
        access_token="token-123",
        refresh_token="refresh-123",
        expires_at=9999999999,
        client_id="cid",
        client_secret="secret",
        tenant="common",
    )

    try:
        client.get_profile()
    except RuntimeError as exc:
        assert "Missing User.Read scope" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
