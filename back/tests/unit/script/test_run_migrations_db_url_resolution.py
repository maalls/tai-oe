from urllib.parse import unquote, urlparse

from script import run_migrations


def _clear_db_env(monkeypatch):
    for key in (
        "MIGRATION_DATABASE_URL",
        "ADMIN_DATABASE_URL",
        "DATABASE_URL",
        "SUPABASE_ENV_FILE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_get_migration_db_url_uses_shared_supabase_env_only(monkeypatch, tmp_path):
    _clear_db_env(monkeypatch)

    shared = tmp_path / ".env.prod"
    shared.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=s3cr3t!",
                "POSTGRES_USER=app_user",
                "POSTGRES_HOST=db.internal",
                "POSTGRES_PORT=5544",
                "POSTGRES_DB=ge_prod",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared))
    monkeypatch.setenv("DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")
    monkeypatch.setenv("ADMIN_DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql://ignored:ignored@ignored:5432/ignored")

    source, db_url = run_migrations.get_migration_db_url()
    parsed = urlparse(db_url)

    assert "SUPABASE_ENV_FILE" == source
    assert "app_user" == parsed.username
    assert "s3cr3t!" == unquote(parsed.password)
    assert "db.internal" == parsed.hostname
    assert 5544 == parsed.port
    assert "ge_prod" == parsed.path.lstrip("/")
