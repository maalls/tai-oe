"""Tests for ClassifyService.handle_classify."""

from service.classification.handler_service import ClassifyService


class _DbHandlerStub:
    def __init__(self, emails):
        self.emails = emails

    def get_email(self, email_id: str):
        return self.emails.get(email_id)


class _RepositoryStub:
    def __init__(self, emails, force_result=None):
        self.db_handler = _DbHandlerStub(emails)
        self.force_calls = []
        self.force_result = force_result or {
            "status": "ok",
            "message": "Email classified successfully",
            "result": {"category": "legacy"},
        }

    def classify_email(self, email_uuid: str, user_id: str, force: bool = False):
        self.force_calls.append((email_uuid, user_id, force))
        return self.force_result


class _WorkflowStub:
    def __init__(self):
        self.calls = []

    def process_new_email(self, email_id: str):
        self.calls.append(email_id)
        return {"email_id": email_id, "category": "quote", "status": "classified"}


class _FactoryStub:
    def __init__(self, workflow):
        self.workflow = workflow

    def create_email_workflow_service(self):
        return self.workflow


def test_handle_classify_uses_workflow_for_unclassified_email():
    emails = {
        "e-1": {"id": "e-1", "user_id": "u-1", "is_classified": False},
    }
    repo = _RepositoryStub(emails)
    workflow = _WorkflowStub()
    service = ClassifyService(service_factory=_FactoryStub(workflow), repository=repo)

    result = service.handle_classify("e-1", "u-1", force=True)

    assert result["status"] == "ok"
    assert result["result"]["category"] == "quote"
    assert workflow.calls == ["e-1"]
    assert repo.force_calls == []


def test_handle_classify_returns_cached_payload_when_already_classified_without_force():
    emails = {
        "e-2": {
            "id": "e-2",
            "user_id": "u-2",
            "is_classified": True,
            "category": "rfq",
            "category_suggestion": "quote",
            "classification_reason": "matched sender",
            "classified_at": "2026-05-13T10:20:30Z",
        },
    }
    repo = _RepositoryStub(emails)
    workflow = _WorkflowStub()
    service = ClassifyService(service_factory=_FactoryStub(workflow), repository=repo)

    result = service.handle_classify("e-2", "u-2", force=False)

    assert result == {
        "status": "ok",
        "message": "Email classified successfully",
        "result": {
            "category": "rfq",
            "category_suggestion": "quote",
            "classification_reason": "matched sender",
            "classified_at": "2026-05-13T10:20:30Z",
        },
    }
    assert workflow.calls == []
    assert repo.force_calls == []


def test_handle_classify_uses_legacy_path_for_forced_reclassification():
    emails = {
        "e-3": {"id": "e-3", "user_id": "u-3", "is_classified": True},
    }
    repo = _RepositoryStub(emails)
    workflow = _WorkflowStub()
    service = ClassifyService(service_factory=_FactoryStub(workflow), repository=repo)

    result = service.handle_classify("e-3", "u-3", force=True)

    assert result["result"]["category"] == "legacy"
    assert repo.force_calls == [("e-3", "u-3", True)]
    assert workflow.calls == []


def test_handle_classify_rejects_unauthorized_user():
    emails = {
        "e-4": {"id": "e-4", "user_id": "owner", "is_classified": False},
    }
    repo = _RepositoryStub(emails)
    workflow = _WorkflowStub()
    service = ClassifyService(service_factory=_FactoryStub(workflow), repository=repo)

    result = service.handle_classify("e-4", "other-user", force=False)

    assert result["status"] == "error"
    assert result["error_code"] == "UNAUTHORIZED"
    assert workflow.calls == []


def test_handle_classify_returns_not_found_error_for_missing_email():
    repo = _RepositoryStub({})
    workflow = _WorkflowStub()
    service = ClassifyService(service_factory=_FactoryStub(workflow), repository=repo)

    result = service.handle_classify("missing", "u-5", force=False)

    assert result["status"] == "error"
    assert result["error_code"] == "EMAIL_NOT_FOUND"
    assert workflow.calls == []
