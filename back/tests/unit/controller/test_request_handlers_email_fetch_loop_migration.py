"""Unit tests for RequestHandlers email fetch loop status migration."""

from src.api.router import RequestHandlers


def test_handle_email_fetch_loop_status_returns_default_when_no_file(tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    status_path = tmp_path / "missing.json"
    legacy_path = tmp_path / "legacy-missing.json"

    result = handlers.handle_email_fetch_loop_status(status_path=status_path, legacy_path=legacy_path)

    assert result == {
        "running": False,
        "pid": None,
        "started_at": None,
        "last_heartbeat": None,
        "mode": None,
    }


def test_handle_email_fetch_loop_status_reads_file_and_detects_running(monkeypatch, tmp_path):
    handlers = RequestHandlers.__new__(RequestHandlers)
    status_path = tmp_path / "email_fetch_loop.json"
    status_path.write_text(
        '{"pid": 1234, "started_at": "2026-01-01T00:00:00", "last_heartbeat": "2026-01-01T00:00:01", "mode": "gmail"}',
        encoding="utf-8",
    )

    calls = []

    def _kill(pid, sig):
        calls.append((pid, sig))
        return None

    monkeypatch.setattr("src.api.router.os.kill", _kill)

    result = handlers.handle_email_fetch_loop_status(status_path=status_path, legacy_path=tmp_path / "legacy.json")

    assert result == {
        "running": True,
        "pid": 1234,
        "started_at": "2026-01-01T00:00:00",
        "last_heartbeat": "2026-01-01T00:00:01",
        "mode": "gmail",
    }
    assert calls == [(1234, 0)]
