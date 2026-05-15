"""Unit tests for run_action_scheduler.main."""

import pytest

from src.command import run_action_scheduler


def test_main_rejects_non_positive_interval():
    with pytest.raises(SystemExit) as exc_info:
        run_action_scheduler.main(["--interval", "0"])

    assert exc_info.value.code == 2


def test_main_exits_when_daemon_flag_used(monkeypatch):
    class _DaemonShouldNotStart:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("daemon should not be instantiated when --daemon is used")

    monkeypatch.setattr(run_action_scheduler, "ActionSchedulerDaemon", _DaemonShouldNotStart)

    with pytest.raises(SystemExit) as exc_info:
        run_action_scheduler.main(["--daemon"])

    assert exc_info.value.code == 1


def test_main_builds_daemon_with_interval_and_starts(monkeypatch):
    captured = {"interval": None, "started": False}

    class _FakeDaemon:
        def __init__(self, interval):
            captured["interval"] = interval

        def start(self):
            captured["started"] = True

    monkeypatch.setattr(run_action_scheduler, "ActionSchedulerDaemon", _FakeDaemon)

    run_action_scheduler.main(["--interval", "30"])

    assert captured["interval"] == 30
    assert captured["started"] is True
