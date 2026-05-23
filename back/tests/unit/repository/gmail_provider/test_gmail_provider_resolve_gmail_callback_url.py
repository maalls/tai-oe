from src.repository.gmail_provider_repository import GmailProviderRepository


def test_resolve_gmail_callback_url_uses_explicit_env_override(monkeypatch):
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "https://api.ai-oe.co/api/gmail/oauth/callback")

    repo = GmailProviderRepository()

    result = repo._resolve_gmail_callback_url()

    assert result == "https://api.ai-oe.co/api/gmail/oauth/callback"


def test_resolve_gmail_callback_url_raises_when_missing(monkeypatch):
    monkeypatch.delenv("GMAIL_OAUTH_CALLBACK_URL", raising=False)

    repo = GmailProviderRepository()

    try:
        repo._resolve_gmail_callback_url()
    except ValueError as exc:
        assert "GMAIL_OAUTH_CALLBACK_URL" in str(exc)
    else:
        raise AssertionError("Expected ValueError when GMAIL_OAUTH_CALLBACK_URL is missing")


def test_resolve_gmail_callback_url_raises_when_invalid(monkeypatch):
    monkeypatch.setenv("GMAIL_OAUTH_CALLBACK_URL", "not-a-url")

    repo = GmailProviderRepository()

    try:
        repo._resolve_gmail_callback_url()
    except ValueError as exc:
        assert "GMAIL_OAUTH_CALLBACK_URL" in str(exc)
    else:
        raise AssertionError("Expected ValueError when GMAIL_OAUTH_CALLBACK_URL is invalid")
