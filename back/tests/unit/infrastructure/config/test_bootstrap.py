from src.infrastructure.config.bootstrap import (
    create_database_service,
    create_db_profile_factory,
    create_runtime_config,
)
from src.infrastructure.config.factory import DbProfileFactory
from src.infrastructure.config.models import ResolvedRuntimeConfig


def _configure_shared_env(monkeypatch, tmp_path):
    shared_env = tmp_path / ".env.prod"
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=pw",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=5544",
                "POSTGRES_DB=ge_prod",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared_env))


def test_create_database_service_returns_database_service_instance(monkeypatch, tmp_path):
    _configure_shared_env(monkeypatch, tmp_path)
    service = create_database_service(current_file=__file__, require_postgres_password=False)
    assert service is not None
    assert service.__class__.__name__ == "DatabaseService"


def test_create_runtime_config_returns_resolved_runtime_config_instance(monkeypatch, tmp_path):
    _configure_shared_env(monkeypatch, tmp_path)
    runtime_config = create_runtime_config(current_file=__file__, require_postgres_password=False)
    assert runtime_config is not None
    assert isinstance(runtime_config, ResolvedRuntimeConfig)


def test_create_db_profile_factory_returns_factory_instance(monkeypatch, tmp_path):
    _configure_shared_env(monkeypatch, tmp_path)
    runtime_config = create_runtime_config(current_file=__file__, require_postgres_password=False)
    profile_factory = create_db_profile_factory(runtime_config)
    assert profile_factory is not None
    assert isinstance(profile_factory, DbProfileFactory)
