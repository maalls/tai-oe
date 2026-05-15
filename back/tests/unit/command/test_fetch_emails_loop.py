"""Unit tests for fetch_emails_loop command behavior."""

from src.command import fetch_emails_loop


def test_run_loop_delegates_to_unified_runner(monkeypatch):
    captured = {}

    def _fake_unified_run_loop(**kwargs):
        captured.update(kwargs)
        return 7

    monkeypatch.setattr(fetch_emails_loop, "unified_run_loop", _fake_unified_run_loop)

    code = fetch_emails_loop.run_loop(
        user_id="u-1",
        interval_seconds=5,
        max_results=10,
        classify_limit=20,
    )

    assert code == 7
    assert captured["user_id"] == "u-1"
    assert captured["interval_seconds"] == 5
    assert captured["max_results"] == 10
    assert captured["classify_limit"] == 20


def test_main_uses_fixed_new_workflow(monkeypatch):
    captured = {}

    def _fake_run_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(fetch_emails_loop, "run_loop", _fake_run_loop)

    fetch_emails_loop.main(["--user-id", "u-2", "--interval", "45"])

    assert captured["user_id"] == "u-2"
    assert captured["interval_seconds"] == 45


def test_main_defaults_match_unified_cli(monkeypatch):
    captured = {}

    def _fake_run_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(fetch_emails_loop, "run_loop", _fake_run_loop)

    fetch_emails_loop.main([])

    assert captured["user_id"] is None
    assert captured["interval_seconds"] == fetch_emails_loop.DEFAULT_INTERVAL_SECONDS
    assert captured["max_results"] == fetch_emails_loop.DEFAULT_MAX_RESULTS
    assert captured["classify_limit"] == fetch_emails_loop.DEFAULT_LOOP_CLASSIFY_LIMIT


def test_main_passes_explicit_limits(monkeypatch):
    captured = {}

    def _fake_run_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(fetch_emails_loop, "run_loop", _fake_run_loop)

    fetch_emails_loop.main(["--max-results", "123", "--classify-limit", "17", "--interval", "60"])

    assert captured["user_id"] is None
    assert captured["interval_seconds"] == 60
    assert captured["max_results"] == 123
    assert captured["classify_limit"] == 17
