"""Unit tests for fetch_emails_loop command behavior."""

import pytest

from src.command import fetch_emails_loop


class _SleepInterrupt:
    def __call__(self, *_args, **_kwargs):
        raise KeyboardInterrupt()


def test_run_loop_single_user_passes_workflow_mode(monkeypatch):
    captured = {}

    def _fake_fetch_emails_run(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(fetch_emails_loop, "fetch_emails_run", _fake_fetch_emails_run)
    monkeypatch.setattr(fetch_emails_loop.time, "sleep", _SleepInterrupt())
    monkeypatch.setattr(fetch_emails_loop, "_write_status", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(fetch_emails_loop, "_clear_status", lambda *_args, **_kwargs: None)

    with pytest.raises(SystemExit) as exc_info:
        fetch_emails_loop.run_loop(
            user_id="u-1",
            interval_seconds=5,
            max_results=10,
            classify_limit=20,
        )

    assert exc_info.value.code == 0
    assert captured["user_id"] == "u-1"

def test_main_uses_fixed_new_workflow(monkeypatch):
    captured = {}

    def _fake_run_loop(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(fetch_emails_loop, "run_loop", _fake_run_loop)

    fetch_emails_loop.main(["--user-id", "u-2", "--interval", "45"])

    assert captured["user_id"] == "u-2"
    assert captured["interval_seconds"] == 45
