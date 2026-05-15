"""Tests for AuthStatusService.get_high_risk_senders."""

from service.email.auth_status_service import AuthStatusService


class _RepoStub:
    db_handler = None


class _AuthHandlerOK:
    def get_high_risk_senders(self, user_id: str, trust_score_threshold: int = 30):
        assert user_id == "u-1"
        assert trust_score_threshold == 30
        return [{"sender_email": "risk@example.com", "trust_score": 10}]


class _AuthHandlerBoom:
    def get_high_risk_senders(self, user_id: str, trust_score_threshold: int = 30):
        raise RuntimeError("boom")


def test_get_high_risk_senders_returns_ok_payload():
    service = AuthStatusService(repository=_RepoStub(), email_auth_handler=_AuthHandlerOK())

    result = service.get_high_risk_senders(user_id="u-1")

    assert result == {
        "status": "ok",
        "data": [{"sender_email": "risk@example.com", "trust_score": 10}],
        "total": 1,
    }


def test_get_high_risk_senders_returns_error_on_exception():
    service = AuthStatusService(repository=_RepoStub(), email_auth_handler=_AuthHandlerBoom())

    result = service.get_high_risk_senders(user_id="u-1")

    assert result["status"] == "error"
    assert result["message"] == "boom"
