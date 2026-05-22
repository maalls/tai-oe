from script import db_create


def test_resolve_db_config_uses_migration_profile(monkeypatch):
    captured = {}

    class _FakeDatabaseService:
        def resolve_migration_db_url(self):
            return (
                "SUPABASE_ENV_FILE",
                "postgresql://app_user:s3cr3t%21@db.internal:5544/ge_prod",
            )

    def _fake_load_runtime_env(*, current_file):
        captured["runtime_current_file"] = current_file

    def _fake_create_database_service(*, current_file, require_postgres_password):
        captured["service_current_file"] = current_file
        captured["require_postgres_password"] = require_postgres_password
        return _FakeDatabaseService()

    monkeypatch.setattr(db_create, "load_runtime_env", _fake_load_runtime_env)
    monkeypatch.setattr(db_create, "create_database_service", _fake_create_database_service)

    resolved = db_create._resolve_db_config()

    assert captured["runtime_current_file"] == db_create.__file__
    assert captured["service_current_file"] == db_create.__file__
    assert captured["require_postgres_password"] is True
    assert resolved == {
        "host": "db.internal",
        "port": 5544,
        "database": "ge_prod",
        "user": "app_user",
        "password": "s3cr3t!",
        "sslmode": "prefer",
    }
