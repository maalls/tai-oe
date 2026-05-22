import src.command.run_migration as run_migration_module


def test_run_migration_delegates_to_canonical_runner(monkeypatch):
    captured = {"reset": None}

    def _fake_run_migrations(*, reset):
        captured["reset"] = reset

    monkeypatch.setattr(run_migration_module, "run_migrations", _fake_run_migrations)

    run_migration_module.run_migration("001_init.sql")

    assert captured["reset"] is False
