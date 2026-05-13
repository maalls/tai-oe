"""Tests for EmailHandlers.handle_classify_unclassified."""

from types import SimpleNamespace

from src.controller.email_handler import EmailHandlers


class _WorkflowOK:
    def __init__(self):
        self.email_service = SimpleNamespace(
            get_all_unclassified=lambda limit, user_id: [SimpleNamespace(id="e-1"), SimpleNamespace(id="e-2")]
        )

    def process_new_email(self, email_id: str):
        return {"email_id": email_id, "status": "classified"}


class _FactoryOK:
    def create_email_workflow_service(self):
        return _WorkflowOK()


class _FactoryBoom:
    def create_email_workflow_service(self):
        raise RuntimeError("boom")


def test_handle_classify_unclassified_new_workflow_success():
    handler = EmailHandlers(service_factory=_FactoryOK())

    result = handler.handle_classify_unclassified(
        user_id="u-1",
        limit=10,
    )

    assert result["status"] == "ok"
    assert result["workflow"] == "new"
    assert result["classified"] == 2
    assert result["skipped"] == 0


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
