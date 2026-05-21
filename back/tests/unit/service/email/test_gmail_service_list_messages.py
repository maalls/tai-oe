"""Unit tests for GmailService.list_messages."""

from src.service.email.gmail_service import GmailService


class _RepoStub:
    def __init__(self):
        self.calls = []

    def fetch_emails(self, **kwargs):
        self.calls.append(kwargs)
        callback = kwargs.get("verify_sender_callback")
        if callback:
            callback(
                user_id="u-1",
                sender_email="sender@example.com",
                sender_name="Sender",
                auth_score=88,
                is_verified=True,
                spf_status="PASS",
                dkim_status="PASS",
                dmarc_status="PASS",
            )
        return {"status": "ok", "messages": []}


class _AuthServiceStub:
    def __init__(self):
        self.calls = []

    def verify_sender(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "ok"}


def test_list_messages_delegates_with_sender_verification_callback():
    repo = _RepoStub()
    auth = _AuthServiceStub()
    service = GmailService(repository=repo, auth_service=auth)

    result = service.list_messages(user_id="u-1", max_results=10, force=True)

    assert result["status"] == "ok"
    assert len(repo.calls) == 1
    assert repo.calls[0]["user_id"] == "u-1"
    assert repo.calls[0]["max_results"] == 10
    assert repo.calls[0]["force"] is True
    assert callable(repo.calls[0]["verify_sender_callback"])
    assert len(auth.calls) == 1
    assert auth.calls[0]["sender_email"] == "sender@example.com"


def test_list_messages_requires_user_id():
    repo = _RepoStub()
    auth = _AuthServiceStub()
    service = GmailService(repository=repo, auth_service=auth)

    result = service.list_messages(user_id="", max_results=10, force=False)

    assert result["status"] == "error"
    assert result["message"] == "Missing user_id"
    assert repo.calls == []
