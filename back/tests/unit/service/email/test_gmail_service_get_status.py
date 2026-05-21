from src.service.email.gmail_service import GmailService


class _ProviderRepoMock:
    def __init__(self):
        self.called = None

    def get_gmail_status(self, user_id=None):
        self.called = user_id
        return {"status": "ok", "authorized": True}


class _EmailRepoMock:
    pass


class _FactoryMock:
    pass


class _AuthMock:
    pass


def test_gmail_service_get_status_uses_provider_repository():
    provider_repo = _ProviderRepoMock()
    service = GmailService(
        repository=_EmailRepoMock(),
        provider_repository=provider_repo,
        service_factory=_FactoryMock(),
        auth_service=_AuthMock(),
    )

    result = service.get_status(user_id="u-1")

    assert result["status"] == "ok"
    assert provider_repo.called == "u-1"
