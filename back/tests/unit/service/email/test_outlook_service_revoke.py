from src.service.email.outlook_service import OutlookService


class _ProviderRepoMock:
    def __init__(self):
        self.called = None

    def revoke_outlook(self, user_id=None):
        self.called = user_id
        return {"status": "ok", "message": "Outlook authorization removed"}


class _EmailRepoMock:
    pass


def test_outlook_service_revoke_delegates_to_provider_repository():
    provider_repo = _ProviderRepoMock()
    service = OutlookService(repository=_EmailRepoMock(), provider_repository=provider_repo)

    result = service.revoke(user_id="u-1")

    assert result == {"status": "ok", "message": "Outlook authorization removed"}
    assert provider_repo.called == "u-1"
