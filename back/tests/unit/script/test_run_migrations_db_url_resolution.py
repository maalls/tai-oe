from urllib.parse import unquote, urlparse

import pytest

from script import run_migrations


def _clear_db_env(monkeypatch):
    for key in (
        "MIGRATION_DATABASE_URL",
        "ADMIN_DATABASE_URL",
        "DATABASE_URL",
        "SUPABASE_ENV_FILE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_get_migration_db_url_prefers_explicit_migration_url(monkeypatch, tmp_path):
    _clear_db_env(monkeypatch)

    shared = tmp_path / ".env.prod"
    shared.write_text("POSTGRES_PASSWORD=from_shared\n", encoding="utf-8")

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres.ge-prod:app@localhost:5432/ge_prod")
    monkeypatch.setenv("ADMIN_DATABASE_URL", "postgresql://admin:pwd@localhost:5432/ge_prod")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://mig:pwd@localhost:5432/ge_prod")

    source, db_url = run_migrations.get_migration_db_url()

    assert "MIGRATION_DATABASE_URL" == source
    assert "postgresql://mig:pwd@localhost:5432/ge_prod" == db_url


def test_get_migration_db_url_prefers_admin_url_over_derived(monkeypatch, tmp_path):
    _clear_db_env(monkeypatch)

    shared = tmp_path / ".env.prod"
    shared.write_text("POSTGRES_PASSWORD=from_shared\n", encoding="utf-8")

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres.ge-prod:app@localhost:5432/ge_prod")
    monkeypatch.setenv("ADMIN_DATABASE_URL", "postgresql://admin:pwd@localhost:5432/ge_prod")

    source, db_url = run_migrations.get_migration_db_url()

    assert "ADMIN_DATABASE_URL" == source
    assert "postgresql://admin:pwd@localhost:5432/ge_prod" == db_url


def test_get_migration_db_url_derives_from_shared_env_with_tenant_suffix(monkeypatch, tmp_path):
    _clear_db_env(monkeypatch)

    shared = tmp_path / ".env.prod"
    shared.write_text("POSTGRES_PASSWORD=s3cr3t!\n", encoding="utf-8")

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres.ge-prod:app@db.internal:5544/ge_prod")

    source, db_url = run_migrations.get_migration_db_url()
    parsed = urlparse(db_url)

    assert "SUPABASE_ENV_FILE" == source
    assert "supabase_admin.ge-prod" == parsed.username
    assert "s3cr3t!" == unquote(parsed.password)
    assert "db.internal" == parsed.hostname
    assert 5544 == parsed.port
    assert "ge_prod" == parsed.path.lstrip("/")


def test_get_migration_db_url_falls_back_to_database_url(monkeypatch, tmp_path):
    _clear_db_env(monkeypatch)

    shared = tmp_path / ".env.prod"
    shared.write_text("ANON_KEY=only_non_db_value\n", encoding="utf-8")

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    monkeypatch.setenv("DATABASE_URL", "postgresql://app:pwd@localhost:5432/ge_prod")

    source, db_url = run_migrations.get_migration_db_url()

    assert "DATABASE_URL" == source
    assert "postgresql://app:pwd@localhost:5432/ge_prod" == db_url


def test_get_migration_db_url_raises_when_no_source(monkeypatch):
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("SUPABASE_ENV_FILE", "/tmp/does-not-exist.supabase.env")

    with pytest.raises(ValueError, match="No PostgreSQL URL configured for migrations"):
        run_migrations.get_migration_db_url()
