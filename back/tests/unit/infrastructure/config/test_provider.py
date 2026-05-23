from pathlib import Path

from src.infrastructure.config.provider import ConfigProvider


def test_provider_resolves_relative_shared_env_path(tmp_path):
    env_file = tmp_path / "back.env"
    shared_dir = tmp_path / "supabase"
    shared_dir.mkdir(parents=True, exist_ok=True)
    shared_env = shared_dir / ".env.prod"

    env_file.write_text("SUPABASE_ENV_FILE=./supabase/.env.prod\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=pw",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={"SUPABASE_ENV_FILE": "./supabase/.env.prod"},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "pw" == resolved.shared.postgres_password


def test_provider_db_hints_allow_local_postgres_overrides(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=6432",
                "POSTGRES_DB=ge_prod",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={"SUPABASE_ENV_FILE": str(shared_env)},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "db.internal" == resolved.db_hints.host
    assert 6432 == resolved.db_hints.port
    assert "ge_prod" == resolved.db_hints.database
    assert "app_user" == resolved.db_hints.username
    assert "prefer" == resolved.db_hints.sslmode
    assert resolved.database_url is None
    assert resolved.migration_database_url is None
    assert resolved.admin_database_url is None


def test_provider_db_hints_prioritize_process_over_local_and_shared(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=6432",
                "POSTGRES_DB=ge_prod",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={"SUPABASE_ENV_FILE": str(shared_env)},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "db.internal" == resolved.db_hints.host
    assert 6432 == resolved.db_hints.port


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
        environ={"SUPABASE_ENV_FILE": str(shared_env)},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "https://shared.example.com" == resolved.supabase_url
    assert "shared-anon" == resolved.supabase_anon_key
    assert "shared-service" == resolved.supabase_service_key


def test_provider_raises_when_supabase_env_file_missing(tmp_path):
    env_file = tmp_path / "back.env"
    env_file.write_text("SUPABASE_ENV_FILE=./supabase/.env.prod\n", encoding="utf-8")

    provider = ConfigProvider(environ={}, env_file_path=env_file, current_file=str(Path(__file__)))

    try:
        provider.resolve()
    except ValueError as exc:
        assert "SUPABASE_ENV_FILE" in str(exc)
    else:
        raise AssertionError("Expected ValueError when SUPABASE_ENV_FILE is missing")


def test_provider_uses_process_env_supabase_env_file_when_local_differs(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env_local = tmp_path / "local.env"
    shared_env_process = tmp_path / "process.env"

    shared_env_local.write_text("POSTGRES_PASSWORD=local_pw\n", encoding="utf-8")
    shared_env_process.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=process_pw",
                "SUPABASE_PUBLIC_URL=https://process.example.com",
                "ANON_KEY=process-anon",
                "SERVICE_ROLE_KEY=process-service",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env_local}\n", encoding="utf-8")

    provider = ConfigProvider(
        environ={"SUPABASE_ENV_FILE": str(shared_env_process)},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
    )

    resolved = provider.resolve()

    assert "process_pw" == resolved.shared.postgres_password
    assert "https://process.example.com" == resolved.supabase_url


def test_provider_can_resolve_in_lenient_mode_without_shared_postgres_password(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "API_EXTERNAL_URL=https://api.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    provider = ConfigProvider(
        environ={"SUPABASE_ENV_FILE": str(shared_env)},
        env_file_path=env_file,
        current_file=str(Path(__file__)),
        require_postgres_password=False,
    )

    resolved = provider.resolve()

    assert "" == resolved.shared.postgres_password
    assert "https://api.example.com" == resolved.supabase_url
