from src.infrastructure.config.factory import DbProfileFactory
from src.infrastructure.config.models import (
    DatabaseRuntimeHints,
    ResolvedRuntimeConfig,
    SharedSupabaseConfig,
)


def _build_resolved_config(*, username: str | None = "postgres") -> ResolvedRuntimeConfig:
    shared = SharedSupabaseConfig(
        postgres_password="shared_pw",
        postgres_user="shared_user",
        postgres_host="shared-db",
        postgres_port=6432,
        postgres_db="shared_db",
    )
    hints = DatabaseRuntimeHints(
        host="runtime-db",
        port=5544,
        database="runtime_db",
        username=username,
        sslmode="require",
        tenant_suffix=None,
    )
    return ResolvedRuntimeConfig(shared=shared, db_hints=hints)


def test_build_app_profile_uses_shared_derived_hints():
    config = _build_resolved_config(username="app_user")

    profile = DbProfileFactory(config).build_app_profile()

    assert "runtime-db" == profile.host
    assert 5544 == profile.port
    assert "runtime_db" == profile.database
    assert "app_user" == profile.user
    assert "shared_pw" == profile.password
    assert "require" == profile.sslmode
    assert "SUPABASE_ENV_FILE" == profile.source


def test_build_app_profile_falls_back_to_shared_user_when_hint_user_missing():
    config = _build_resolved_config(username=None)

    profile = DbProfileFactory(config).build_app_profile()

    assert "shared_user" == profile.user


def test_build_migration_profile_matches_app_profile():
    config = _build_resolved_config(username="app_user")
    factory = DbProfileFactory(config)

    app_profile = factory.build_app_profile()
    migration_profile = factory.build_migration_profile(
        migration_database_url="postgresql://ignored",
        admin_database_url="postgresql://ignored",
        database_url="postgresql://ignored",
    )

    assert app_profile == migration_profile


def test_get_configured_database_url_returns_none_for_all_sources():
    config = _build_resolved_config()
    factory = DbProfileFactory(config)

    assert factory.get_configured_database_url("MIGRATION_DATABASE_URL") is None
    assert factory.get_configured_database_url("ADMIN_DATABASE_URL") is None
    assert factory.get_configured_database_url("DATABASE_URL") is None
