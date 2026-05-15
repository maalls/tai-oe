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
