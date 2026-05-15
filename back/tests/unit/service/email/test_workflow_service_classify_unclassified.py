"""Unit tests for EmailWorkflowService.classify_unclassified."""

from types import SimpleNamespace

from service.email.workflow_service import EmailWorkflowService


class _EmailServiceStub:
    def __init__(self, emails):
        self.emails = emails
        self.calls = []

    def get_all_unclassified(self, limit: int = 100, user_id=None):
        self.calls.append((limit, user_id))
        return self.emails


def test_classify_unclassified_returns_error_without_user_id():
    workflow = EmailWorkflowService(
        email_service=_EmailServiceStub([]),
        classification_service=object(),
    )

    result = workflow.classify_unclassified(user_id="", limit=10)

    assert result["status"] == "error"
    assert "user_id" in result["message"]


def test_classify_unclassified_processes_all_and_collects_errors():
    emails = [SimpleNamespace(id="e-1"), SimpleNamespace(id="e-2"), SimpleNamespace(id="e-3")]
    email_service = _EmailServiceStub(emails)
    workflow = EmailWorkflowService(
        email_service=email_service,
        classification_service=object(),
    )

    processed = []

    def _process(email_id: str):
        processed.append(email_id)
        if email_id == "e-2":
            raise RuntimeError("boom")
        return {"email_id": email_id, "status": "classified"}

    workflow.process_new_email = _process

    result = workflow.classify_unclassified(user_id="u-1", limit=25)

    assert result["status"] == "ok"
    assert result["workflow"] == "new"
    assert result["classified"] == 2
    assert result["skipped"] == 1
    assert result["errors"] == [{"email_id": "e-2", "error": "boom"}]
    assert email_service.calls == [(25, "u-1")]
    assert processed == ["e-1", "e-2", "e-3"]
