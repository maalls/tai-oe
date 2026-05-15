"""Tests for EmailHandlers.handle_classify_unclassified."""

from types import SimpleNamespace

from src.api.email.handler import EmailHandlers


class _WorkflowOK:
    def __init__(self):
        self.calls = []

    def classify_unclassified(self, user_id: str, limit: int = 200):
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
            }
        self.calls.append((user_id, limit))
        return {
            "status": "ok",
            "workflow": "new",
            "classified": 2,
            "skipped": 0,
            "errors": [],
        }


class _FactoryOK:
    def create_email_workflow_service(self):
        return _WorkflowOK()


class _FactoryBoom:
    def create_email_workflow_service(self):
        raise RuntimeError("boom")


def test_handle_classify_unclassified_new_workflow_success():
    workflow = _WorkflowOK()
    handler = EmailHandlers(service_factory=SimpleNamespace(create_email_workflow_service=lambda: workflow))

    result = handler.handle_classify_unclassified(
        user_id="u-1",
        limit=10,
    )

    assert result["status"] == "ok"
    assert result["workflow"] == "new"
    assert result["classified"] == 2
    assert result["skipped"] == 0
    assert workflow.calls == [("u-1", 10)]


def test_handle_classify_unclassified_new_workflow_fail_fast():
    handler = EmailHandlers(service_factory=_FactoryBoom())

    result = handler.handle_classify_unclassified(
        user_id="u-2",
        limit=5,
    )

    assert result["status"] == "error"
    assert result["workflow"] == "new"
    assert "failed" in result["message"].lower()


def test_handle_classify_unclassified_requires_user_id():
    handler = EmailHandlers(service_factory=_FactoryOK())

    result = handler.handle_classify_unclassified(user_id="", limit=5)

    assert result["status"] == "error"
    assert "user_id" in result["message"]
