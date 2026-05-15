"""Unit tests for fetch_emails.run."""

from src.command import fetch_emails


def test_run_delegates_to_unified_runner(monkeypatch):
    captured = {}

    def _fake_unified_runner(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(fetch_emails, "unified_run_fetch_emails", _fake_unified_runner)

    code = fetch_emails.run(
        user_id="u-1",
        max_results=42,
        classify_limit=10,
        after_date="2026/05/01",
    )

    assert code == 0
    assert captured == {
        "user_id": "u-1",
        "max_results": 42,
        "classify_limit": 10,
        "after_date": "2026/05/01",
    }


def test_run_ignores_legacy_workflow_argument(monkeypatch):
    def _fake_unified_runner(**_kwargs):
        return 0

    monkeypatch.setattr(fetch_emails, "unified_run_fetch_emails", _fake_unified_runner)

    code = fetch_emails.run(user_id="u-1", workflow=object())

    assert code == 0


def test_run_propagates_unified_runner_exit_code(monkeypatch):
    def _fake_unified_runner(**_kwargs):
        return 1

    monkeypatch.setattr(fetch_emails, "unified_run_fetch_emails", _fake_unified_runner)

    code = fetch_emails.run(user_id="u-1")

    assert code == 1
