"""Unit tests for fetch_emails.run."""

from types import SimpleNamespace

from src.command import fetch_emails


class _LegacyRepoOK:
    def fetch_and_process_emails(self, **kwargs):
        return {
            "status": "ok",
            "emails_fetched": 2,
            "emails_classified": 1,
            "contacts_created": 0,
            "accounts_created": 0,
            "rfq_processed": 0,
            "opportunities_created": 0,
            "quotes_generated": 0,
            "errors": [],
        }


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


def test_run_legacy_mode_success(monkeypatch):
    monkeypatch.setattr(fetch_emails, "_get_legacy_repo", lambda: _LegacyRepoOK())

    code = fetch_emails.run(user_id="u-1", use_new_workflow=False)

    assert code == 0


def test_run_new_workflow_success(monkeypatch):
    monkeypatch.setattr("src.infrastructure.factory.ServiceFactory", _FactoryOK)

    code = fetch_emails.run(user_id="u-1", classify_limit=10, use_new_workflow=True)

    assert code == 0


def test_run_new_workflow_falls_back_to_legacy(monkeypatch):
    class _FactoryBoom:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("factory error")

    monkeypatch.setattr(fetch_emails, "_get_legacy_repo", lambda: _LegacyRepoOK())
    monkeypatch.setattr("src.infrastructure.factory.ServiceFactory", _FactoryBoom)

    code = fetch_emails.run(user_id="u-1", use_new_workflow=True)

    assert code == 0
