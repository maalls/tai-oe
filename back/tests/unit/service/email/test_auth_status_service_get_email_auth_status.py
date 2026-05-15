"""Tests for AuthStatusService.get_email_auth_status."""

from service.email.auth_status_service import AuthStatusService


class _DbHandlerStub:
    def __init__(self, email=None, error=None):
        self.email = email
        self.error = error

    def get_email(self, email_id: str, user_id: str):
        if self.error:
            raise self.error
        return self.email


class _RepoStub:
    def __init__(self, email=None, error=None):
        self.db_handler = _DbHandlerStub(email=email, error=error)


class _AuthHandlerStub:
    def get_high_risk_senders(self, user_id: str, trust_score_threshold: int = 30):
        return []

    def get_verified_senders(self, user_id: str, limit: int = 50):
        return []


def test_get_email_auth_status_returns_ok_payload():
    repo = _RepoStub(
        email={
            "from_email": "a@example.com",
            "from_name": "Alice",
            "spf_status": "PASS",
            "dkim_status": "PASS",
            "dmarc_status": "PASS",
            "auth_score": 95,
            "is_verified": True,
            "sender_verified_at": "2026-05-15T10:00:00",
        }
    )
    service = AuthStatusService(repository=repo, email_auth_handler=_AuthHandlerStub())

    result = service.get_email_auth_status(email_id="e-1", user_id="u-1")

    assert result["status"] == "ok"
    assert result["data"]["email_id"] == "e-1"
    assert result["data"]["from_email"] == "a@example.com"
    assert result["data"]["auth_score"] == 95
    assert result["data"]["is_verified"] is True


def test_get_email_auth_status_returns_not_found():
    service = AuthStatusService(repository=_RepoStub(email=None), email_auth_handler=_AuthHandlerStub())

    result = service.get_email_auth_status(email_id="e-404", user_id="u-1")

    assert result == {"status": "error", "message": "Email not found"}


def test_get_email_auth_status_returns_error_on_exception():
    service = AuthStatusService(
        repository=_RepoStub(error=RuntimeError("db down")),
        email_auth_handler=_AuthHandlerStub(),
    )

    result = service.get_email_auth_status(email_id="e-1", user_id="u-1")

    assert result["status"] == "error"
    assert result["message"] == "db down"
