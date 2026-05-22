from urllib.parse import unquote, urlparse

from src.infrastructure.config.factory import DbProfileFactory
from src.infrastructure.config.models import (
    DatabaseRuntimeHints,
    ResolvedRuntimeConfig,
    SharedSupabaseConfig,
)


def _build_resolved_config(*, username: str | None = "postgres.ge-prod") -> ResolvedRuntimeConfig:
    shared = SharedSupabaseConfig(
        postgres_password="shared_pw",
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
        tenant_suffix="ge-prod" if username and "." in username else None,
    )
    return ResolvedRuntimeConfig(shared=shared, db_hints=hints)


def test_build_app_profile_uses_runtime_hints():
    config = _build_resolved_config()

    profile = DbProfileFactory(config).build_app_profile()

    assert "runtime-db" == profile.host
    assert 5544 == profile.port
    assert "runtime_db" == profile.database
    assert "postgres.ge-prod" == profile.user
    assert "require" == profile.sslmode


def test_build_app_profile_falls_back_to_shared_when_runtime_user_missing():
    config = _build_resolved_config(username=None)

    profile = DbProfileFactory(config).build_app_profile()

    assert "runtime-db" == profile.host
    assert 5544 == profile.port
    assert "runtime_db" == profile.database
    assert "postgres" == profile.user


def test_build_migration_profile_uses_explicit_migration_database_url():
    config = _build_resolved_config()
    explicit_url = "postgresql://mig_user:mig_pw@mig-db:5555/mig_db?sslmode=disable"

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=explicit_url,
        admin_database_url="postgresql://admin:pw@admin-db:5444/admin_db",
        database_url="postgresql://app:pw@app-db:5432/app_db",
    )

    assert "mig-db" == profile.host
    assert 5555 == profile.port
    assert "mig_db" == profile.database
    assert "mig_user" == profile.user
    assert "disable" == profile.sslmode


def test_build_migration_profile_uses_admin_database_url_when_migration_missing():
    config = _build_resolved_config()

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=None,
        admin_database_url="postgresql://admin:pw@admin-db:5444/admin_db?sslmode=prefer",
        database_url="postgresql://app:pw@app-db:5432/app_db",
    )

    assert "admin-db" == profile.host
    assert 5444 == profile.port
    assert "admin_db" == profile.database
    assert "admin" == profile.user


def test_build_migration_profile_derives_tenant_aware_supabase_admin():
    config = _build_resolved_config(username="postgres.ge-prod")

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=None,
        admin_database_url=None,
        database_url="postgresql://postgres.ge-prod:app_pw@localhost:5432/ge_prod",
    )

    assert "localhost" == profile.host
    assert 5432 == profile.port
    assert "ge_prod" == profile.database
    assert "supabase_admin.ge-prod" == profile.user
    assert "shared_pw" == profile.password


def test_build_migration_profile_derives_plain_supabase_admin_without_tenant():
    config = _build_resolved_config(username="postgres")

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=None,
        admin_database_url=None,
        database_url="postgresql://postgres:app_pw@localhost:5432/ge_prod",
    )

    assert "supabase_admin" == profile.user
    assert "shared_pw" == profile.password


def test_build_migration_profile_falls_back_to_shared_hints_when_no_database_url():
    config = _build_resolved_config(username=None)

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=None,
        admin_database_url=None,
        database_url=None,
    )

    assert "runtime-db" == profile.host
    assert 5544 == profile.port
    assert "runtime_db" == profile.database
    assert "supabase_admin" == profile.user


def test_build_migration_profile_handles_url_encoding_for_password():
    shared = SharedSupabaseConfig(
        postgres_password="p@ss/with:special#chars",
        postgres_host="db",
        postgres_port=5432,
        postgres_db="ge_prod",
    )
    hints = DatabaseRuntimeHints(
        host="db",
        port=5432,
        database="ge_prod",
        username="postgres.ge-prod",
        sslmode="prefer",
        tenant_suffix="ge-prod",
    )
    config = ResolvedRuntimeConfig(shared=shared, db_hints=hints)

    profile = DbProfileFactory(config).build_migration_profile(
        migration_database_url=None,
        admin_database_url=None,
        database_url="postgresql://postgres.ge-prod:app_pw@localhost:5432/ge_prod",
    )
    parsed = urlparse(profile.to_url())

    assert "supabase_admin.ge-prod" == parsed.username
    assert "p@ss/with:special#chars" == unquote(parsed.password)
