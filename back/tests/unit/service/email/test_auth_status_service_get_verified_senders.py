"""Tests for AuthStatusService.get_verified_senders."""

from service.email.auth_status_service import AuthStatusService


class _RepoStub:
    db_handler = None


class _AuthHandlerOK:
    def get_verified_senders(self, user_id: str, limit: int = 50):
        assert user_id == "u-1"
        assert limit == 50
        return [{"sender_email": "safe@example.com", "trust_score": 99}]


class _AuthHandlerBoom:
    def get_verified_senders(self, user_id: str, limit: int = 50):
        raise RuntimeError("boom")


def test_get_verified_senders_returns_ok_payload():
    service = AuthStatusService(repository=_RepoStub(), email_auth_handler=_AuthHandlerOK())

    result = service.get_verified_senders(user_id="u-1")

    assert result == {
        "status": "ok",
        "data": [{"sender_email": "safe@example.com", "trust_score": 99}],
        "total": 1,
    }


def test_get_verified_senders_returns_error_on_exception():
    service = AuthStatusService(repository=_RepoStub(), email_auth_handler=_AuthHandlerBoom())

    result = service.get_verified_senders(user_id="u-1")

    assert result["status"] == "error"
    assert result["message"] == "boom"
