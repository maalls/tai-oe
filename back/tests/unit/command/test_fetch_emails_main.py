"""Unit tests for fetch_emails.main."""

import pytest

from src.command import fetch_emails


def test_main_exits_with_code_2_when_user_id_missing(monkeypatch):
    monkeypatch.setattr(fetch_emails, "default_user_id", None)

    with pytest.raises(SystemExit) as exc_info:
        fetch_emails.main([])

    assert exc_info.value.code == 2


def test_main_uses_default_user_id_when_argument_missing(monkeypatch):
    captured = {}

    def _fake_run(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(fetch_emails, "default_user_id", "u-default")
    monkeypatch.setattr(fetch_emails, "run", _fake_run)

    with pytest.raises(SystemExit) as exc_info:
        fetch_emails.main(["--max-results", "77", "--classify-limit", "9"])

    assert exc_info.value.code == 0
    assert captured == {
        "user_id": "u-default",
        "max_results": 77,
        "classify_limit": 9,
        "after_date": None,
    }


def test_main_passes_explicit_user_and_after_date(monkeypatch):
    captured = {}

    def _fake_run(**kwargs):
        captured.update(kwargs)
        return 1

    monkeypatch.setattr(fetch_emails, "run", _fake_run)

    with pytest.raises(SystemExit) as exc_info:
        fetch_emails.main([
            "--user-id",
            "u-explicit",
            "--max-results",
            "12",
            "--classify-limit",
            "5",
            "--after-date",
            "2026/05/01",
        ])

    assert exc_info.value.code == 1
    assert captured == {
        "user_id": "u-explicit",
        "max_results": 12,
        "classify_limit": 5,
        "after_date": "2026/05/01",
    }
