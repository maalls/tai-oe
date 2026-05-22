from pathlib import Path

from src.infrastructure.config.provider import ConfigProvider


def test_provider_resolves_relative_shared_env_path(tmp_path):
    env_file = tmp_path / "back.env"
    shared_dir = tmp_path / "supabase"
    shared_dir.mkdir(parents=True, exist_ok=True)
    shared_env = shared_dir / ".env.prod"

    env_file.write_text("SUPABASE_ENV_FILE=./supabase/.env.prod\n", encoding="utf-8")
    shared_env.write_text("POSTGRES_PASSWORD=pw\n", encoding="utf-8")

    provider = ConfigProvider(
        environ={},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "pw" == resolved.shared.postgres_password


def test_provider_prefers_process_env_over_shared_for_supabase_keys(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={
            "SUPABASE_URL": "https://process.example.com",
            "SUPABASE_ANON_KEY": "process-anon",
            "SUPABASE_SERVICE_KEY": "process-service",
            "DATABASE_URL": "postgresql://postgres.ge-prod:pwd@localhost:5432/ge_prod",
        },
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "https://process.example.com" == resolved.supabase_url
    assert "process-anon" == resolved.supabase_anon_key
    assert "process-service" == resolved.supabase_service_key
    assert "postgres.ge-prod" == resolved.db_hints.username


def test_provider_uses_shared_supabase_values_when_process_env_missing(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "API_EXTERNAL_URL=https://api.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
                "POSTGRES_HOST=db",
                "POSTGRES_PORT=6432",
                "POSTGRES_DB=ge_prod",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "https://api.example.com" == resolved.supabase_url
    assert "shared-anon" == resolved.supabase_anon_key
    assert "shared-service" == resolved.supabase_service_key
    assert "db" == resolved.db_hints.host
    assert 6432 == resolved.db_hints.port
    assert "ge_prod" == resolved.db_hints.database


def test_provider_prefers_database_url_for_db_hints_over_shared_defaults(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "POSTGRES_HOST=shared-host",
                "POSTGRES_PORT=5432",
                "POSTGRES_DB=shared_db",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={
            "DATABASE_URL": "postgresql://postgres.ge-prod:pwd@db.internal:5544/live_db?sslmode=require"
        },
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "db.internal" == resolved.db_hints.host
    assert 5544 == resolved.db_hints.port
    assert "live_db" == resolved.db_hints.database
    assert "require" == resolved.db_hints.sslmode
    assert "ge-prod" == resolved.db_hints.tenant_suffix
