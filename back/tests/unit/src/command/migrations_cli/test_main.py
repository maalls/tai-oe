import src.command.migrations_cli as migrations_cli


def test_main_delegates_to_run_migrations(monkeypatch):
    captured = {"reset": None}

    def _fake_run_migrations(*, reset):
        captured["reset"] = reset

    monkeypatch.setattr(migrations_cli, "run_migrations", _fake_run_migrations)
    monkeypatch.setattr(migrations_cli.sys, "argv", ["migrations_cli.py", "--reset"])

    result = migrations_cli.main()

    assert 0 == result
    assert captured["reset"] is True
