from src.repository.outlook_provider_repository import OutlookProviderRepository


class _OutlookClientMock:
    def __init__(self):
        self.called = False

    def get_profile(self):
        self.called = True
        return {"displayName": "John"}


def test_get_outlook_status_returns_authorized_when_profile_fetch_works(monkeypatch):
    client = _OutlookClientMock()

    def _fake_get_outlook_client(self, user_id):
        assert user_id == "user-1"
        return client, None

    monkeypatch.setattr(
        "src.repository.outlook_provider_repository.OutlookProviderRepository._get_outlook_client",
        _fake_get_outlook_client,
    )

    repo = OutlookProviderRepository()

    result = repo.get_outlook_status("user-1")

    assert result == {"status": "ok", "authorized": True, "message": "Outlook authorized"}
    assert client.called is True
