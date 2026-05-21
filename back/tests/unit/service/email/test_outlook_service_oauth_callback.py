from src.service.email.outlook_service import OutlookService


class _ProviderRepoMock:
    def __init__(self):
        self.called = None

    def handle_outlook_oauth_callback(self, code, state=None):
        self.called = (code, state)
        return {"status": "ok", "redirect_url": "http://localhost:7153/settings"}


class _EmailRepoMock:
    pass


def test_outlook_service_oauth_callback_delegates_to_provider_repository():
    provider_repo = _ProviderRepoMock()
    service = OutlookService(repository=_EmailRepoMock(), provider_repository=provider_repo)

    result = service.oauth_callback(code="code-1", state="state-1")

    assert result == {"status": "ok", "redirect_url": "http://localhost:7153/settings"}
    assert provider_repo.called == ("code-1", "state-1")
