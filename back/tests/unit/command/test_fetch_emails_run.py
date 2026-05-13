"""Unit tests for fetch_emails.run."""

from types import SimpleNamespace
import pytest

from src.command import fetch_emails


class _WorkflowOK:
    def __init__(self):
        self.email_service = SimpleNamespace(
            get_all_unclassified=lambda limit, user_id: [SimpleNamespace(id="e-1"), SimpleNamespace(id="e-2")]
        )

    def process_new_email(self, email_id: str):
        return {"email_id": email_id, "category": "quote", "status": "classified"}


class _FactoryOK:
    def create_email_workflow_service(self):
        return _WorkflowOK()


def test_run_new_workflow_success(monkeypatch):
    monkeypatch.setattr("src.infrastructure.factory.ServiceFactory", _FactoryOK)

    code = fetch_emails.run(user_id="u-1", classify_limit=10)

    assert code == 0


def test_run_new_workflow_fails_fast_without_legacy_fallback(monkeypatch):
    class _FactoryBoom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("factory error")

    monkeypatch.setattr("src.infrastructure.factory.ServiceFactory", _FactoryBoom)

    with pytest.raises(RuntimeError, match="factory error"):
        fetch_emails.run(user_id="u-1")
