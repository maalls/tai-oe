"""Unit tests for fetch_all_users_emails wrapper."""

from src.command import fetch_all_users_emails


def test_main_delegates_to_unified_fetch_all_with_explicit_args(monkeypatch):
    captured = {}

    def _fake_fetch_for_all_users(**kwargs):
        captured.update(kwargs)
        return 9

    monkeypatch.setattr(fetch_all_users_emails, "fetch_for_all_users", _fake_fetch_for_all_users)

    code = fetch_all_users_emails.main(["--max-results", "77", "--user-id", "u-9"])

    assert code == 9
    assert captured == {"max_results": 77, "user_id": "u-9"}


def test_main_delegates_with_defaults(monkeypatch):
    captured = {}

    def _fake_fetch_for_all_users(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(fetch_all_users_emails, "fetch_for_all_users", _fake_fetch_for_all_users)

    code = fetch_all_users_emails.main([])

    assert code == 0
    assert captured["max_results"] == fetch_all_users_emails.DEFAULT_MAX_RESULTS
    assert captured["user_id"] is None
