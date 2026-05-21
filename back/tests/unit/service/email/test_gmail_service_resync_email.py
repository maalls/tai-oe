"""Unit tests for GmailService.resync_email."""

from src.service.email.gmail_service import GmailService


class _RepoStub:
    def __init__(self):
        self.calls = []

    def resync_email_from_gmail(self, **kwargs):
        self.calls.append(kwargs)
        callback = kwargs.get("verify_sender_callback")
        if callback:
            callback(
                user_id=kwargs["user_id"],
                sender_email="sender@example.com",
                sender_name="Sender",
                auth_score=75,
                is_verified=False,
                spf_status="PASS",
                dkim_status="FAIL",
                dmarc_status="NONE",
            )
        return {"status": "ok", "email_id": kwargs["email_id"]}


class _AuthServiceStub:
    def __init__(self):
        self.calls = []

    def verify_sender(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "ok"}


def test_resync_email_delegates_with_sender_verification_callback():
    repo = _RepoStub()
    auth = _AuthServiceStub()
    service = GmailService(repository=repo, auth_service=auth)

    result = service.resync_email(email_id="e-1", provider_message_id="m-1", user_id="u-1")

    assert result["status"] == "ok"
    assert len(repo.calls) == 1
    assert repo.calls[0]["email_id"] == "e-1"
    assert repo.calls[0]["provider_message_id"] == "m-1"
    assert repo.calls[0]["user_id"] == "u-1"
    assert callable(repo.calls[0]["verify_sender_callback"])
    assert len(auth.calls) == 1
    assert auth.calls[0]["user_id"] == "u-1"


def test_resync_email_requires_provider_message_id():
    repo = _RepoStub()
    auth = _AuthServiceStub()
    service = GmailService(repository=repo, auth_service=auth)

    result = service.resync_email(email_id="e-1", provider_message_id="", user_id="u-1")

    assert result["status"] == "error"
    assert result["message"] == "Missing provider_message_id"
    assert repo.calls == []
