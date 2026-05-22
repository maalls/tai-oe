from src.infrastructure.clients.database import DatabaseHandler


def test_get_db_config_reads_shared_supabase_env(monkeypatch, tmp_path):
    shared = tmp_path / ".env.prod"
    shared.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=env_pass",
                "POSTGRES_USER=env_user",
                "POSTGRES_HOST=localhost",
                "POSTGRES_PORT=5432",
                "POSTGRES_DB=ge_prod",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    fake_database_service = object()

    handler = DatabaseHandler(
        config={
            "supabase": {
                "db": {
                    "host": "yaml-host",
                    "port": 5432,
                    "user": "yaml-user",
                    "password": "yaml-pass",
                }
            }
        },
        database_service=fake_database_service,
    )

    assert "env_user" == handler.db_config["user"]
    assert "env_pass" == handler.db_config["password"]
    assert "localhost" == handler.db_config["host"]
    assert 5432 == handler.db_config["port"]
    assert "ge_prod" == handler.db_config["database"]
    assert "prefer" == handler.db_config["sslmode"]
