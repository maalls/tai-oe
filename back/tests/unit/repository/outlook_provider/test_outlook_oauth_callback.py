from src.repository.outlook_provider_repository import OutlookProviderRepository


class _TokenRepositoryMock:
    def __init__(self):
        self.saved = None

    def set_token_json(self, user_id, provider, service, token_json, scope=None, expires_at=None):
        self.saved = {
            "user_id": user_id,
            "provider": provider,
            "service": service,
            "token_json": token_json,
            "scope": scope,
            "expires_at": expires_at,
        }
        return True


def test_handle_outlook_oauth_callback_saves_tokens(monkeypatch):
    def _fake_callback(code, state=None):
        assert code == "auth-code-1"
        assert state == "state-1"
        return {
            "status": "ok",
            "tokens": {
                "access_token": "acc",
                "refresh_token": "ref",
                "expires_at": 12345,
                "scope": "Mail.Read Mail.Send offline_access",
            },
            "user_id": "user-1",
            "redirect_url": "http://localhost:7153/settings",
        }

    monkeypatch.setattr(
        "src.repository.outlook_provider_repository.handle_outlook_oauth_callback",
        _fake_callback,
    )

    token_repo = _TokenRepositoryMock()
    repo = OutlookProviderRepository(oauth_token_repository=token_repo)

    result = repo.handle_outlook_oauth_callback("auth-code-1", "state-1")

    assert result == {
        "status": "ok",
        "redirect_url": "http://localhost:7153/settings",
        "user_id": "user-1",
    }
    assert token_repo.saved["user_id"] == "user-1"
    assert token_repo.saved["provider"] == "microsoft"
    assert token_repo.saved["service"] == "mail"
    assert token_repo.saved["scope"] == "Mail.Read Mail.Send offline_access"
    assert token_repo.saved["expires_at"] == 12345
