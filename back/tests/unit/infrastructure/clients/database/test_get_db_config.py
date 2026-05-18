from src.infrastructure.clients.database import DatabaseHandler


def test_get_db_config_prefers_database_url(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://env_user:env_pass@localhost:5432/ge_prod?sslmode=disable",
    )

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
        }
    )

    assert "env_user" == handler.db_config["user"]
    assert "env_pass" == handler.db_config["password"]
    assert "localhost" == handler.db_config["host"]
    assert 5432 == handler.db_config["port"]
    assert "ge_prod" == handler.db_config["database"]
    assert "disable" == handler.db_config["sslmode"]
