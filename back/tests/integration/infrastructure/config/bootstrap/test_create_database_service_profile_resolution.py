from urllib.parse import unquote, urlparse

import src.infrastructure.config.service as config_service_module
from src.infrastructure.config.bootstrap import create_database_service


def test_create_database_service_resolves_migration_profile_from_shared_env(monkeypatch, tmp_path):
    shared_env = tmp_path / ".env.prod"
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=s3cr3t!",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=5544",
                "POSTGRES_DB=ge_prod",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared_env))
    monkeypatch.setenv("DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")
    monkeypatch.setenv("ADMIN_DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")

    service = create_database_service(
        current_file=__file__,
        require_postgres_password=True,
    )

    source, db_url = service.resolve_migration_db_url()
    parsed = urlparse(db_url)

    assert source == "SUPABASE_ENV_FILE"
    assert parsed.username == "app_user"
    assert unquote(parsed.password) == "s3cr3t!"
    assert parsed.hostname == "db.internal"
    assert parsed.port == 5544
    assert parsed.path.lstrip("/") == "ge_prod"


def test_create_database_service_uses_app_profile_on_connect(monkeypatch, tmp_path):
    shared_env = tmp_path / ".env.prod"
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=app-pass",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=5544",
                "POSTGRES_DB=ge_prod",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared_env))

    captured = {}

    def _fake_connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(config_service_module.psycopg2, "connect", _fake_connect)

    service = create_database_service(
        current_file=__file__,
        require_postgres_password=True,
    )

    _ = service.connect(profile_name="app")

    assert captured == {
        "host": "db.internal",
        "port": 5544,
        "database": "ge_prod",
        "user": "app_user",
        "password": "app-pass",
        "sslmode": "prefer",
    }
