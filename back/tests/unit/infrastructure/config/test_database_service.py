from types import SimpleNamespace

import pytest

from src.infrastructure.config.factory import DbProfileFactory
from src.infrastructure.config.models import (
    DatabaseRuntimeHints,
    ResolvedRuntimeConfig,
    SharedSupabaseConfig,
)
from src.infrastructure.config.service import DatabaseService


class FakeCursor:
    def __init__(self):
        self.closed = False
        self._fetchone_result = None
        self.executed = []

    def set_fetchone_result(self, value):
        self._fetchone_result = value

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self._fetchone_result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


class RecordingConnector:
    def __init__(self):
        self.calls = []
        self.connection = FakeConnection()

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.connection


def _runtime_config() -> ResolvedRuntimeConfig:
    return ResolvedRuntimeConfig(
        shared=SharedSupabaseConfig(
            postgres_password="shared_pw",
            postgres_host="shared-db",
            postgres_port=5432,
            postgres_db="ge_prod",
        ),
        db_hints=DatabaseRuntimeHints(
            host="runtime-db",
            port=5433,
            database="runtime",
            username="postgres.ge-prod",
            sslmode="require",
            tenant_suffix="ge-prod",
        ),
    )


def test_connect_uses_app_profile_by_default():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    conn = service.connect()

    assert conn is connector.connection
    assert 1 == len(connector.calls)
    kwargs = connector.calls[0]
    assert "runtime-db" == kwargs["host"]
    assert 5433 == kwargs["port"]
    assert "runtime" == kwargs["database"]
    assert "postgres.ge-prod" == kwargs["user"]
    assert "shared_pw" == kwargs["password"]
    assert "require" == kwargs["sslmode"]


def test_connect_can_use_explicit_migration_profile():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    conn = service.connect(
        profile_name="migration",
        migration_database_url=None,
        admin_database_url=None,
        database_url="postgresql://postgres.ge-prod:app_pw@localhost:5432/ge_prod",
    )

    assert conn is connector.connection
    kwargs = connector.calls[0]
    assert "supabase_admin.ge-prod" == kwargs["user"]
    assert "shared_pw" == kwargs["password"]


def test_cursor_context_closes_cursor_and_connection():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    with service.cursor(profile_name="app") as cursor:
        assert cursor is connector.connection.cursor_instance

    assert connector.connection.cursor_instance.closed is True
    assert connector.connection.closed is True


def test_connect_raises_for_unknown_profile_name():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    with pytest.raises(ValueError, match="Unsupported profile_name"):
        service.connect(profile_name="unknown")


def test_create_migration_db_uses_migration_profile():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    conn = service.create_migration_db()

    assert conn is connector.connection
    kwargs = connector.calls[0]
    assert "supabase_admin.ge-prod" == kwargs["user"]


def test_resolve_migration_db_url_prefers_explicit_source_from_config():
    connector = RecordingConnector()
    runtime = _runtime_config()
    runtime = ResolvedRuntimeConfig(
        shared=runtime.shared,
        db_hints=runtime.db_hints,
        migration_database_url="postgresql://mig:pw@mig-db:5544/mig_db",
        admin_database_url=None,
        database_url="postgresql://app:pw@app-db:5432/app_db",
    )
    service = DatabaseService(
        profile_factory=DbProfileFactory(runtime),
        connector=connector,
    )

    source, db_url = service.resolve_migration_db_url()

    assert "MIGRATION_DATABASE_URL" == source
    assert "postgresql://mig:pw@mig-db:5544/mig_db" == db_url


def test_resolve_migration_db_url_raises_when_no_source_available():
    connector = RecordingConnector()
    runtime = ResolvedRuntimeConfig(
        shared=SharedSupabaseConfig(postgres_password=""),
        db_hints=DatabaseRuntimeHints(
            host="runtime-db",
            port=5544,
            database="runtime_db",
            username=None,
            sslmode="prefer",
            tenant_suffix=None,
        ),
        migration_database_url=None,
        admin_database_url=None,
        database_url=None,
    )
    service = DatabaseService(
        profile_factory=DbProfileFactory(runtime),
        connector=connector,
    )

    with pytest.raises(ValueError, match="No PostgreSQL URL configured for migrations"):
        service.resolve_migration_db_url()


def test_resolve_masked_migration_db_url_masks_password():
    connector = RecordingConnector()
    runtime = _runtime_config()
    runtime = ResolvedRuntimeConfig(
        shared=runtime.shared,
        db_hints=runtime.db_hints,
        migration_database_url="postgresql://mig:supersecret@mig-db:5544/mig_db",
        admin_database_url=None,
        database_url=None,
    )
    service = DatabaseService(
        profile_factory=DbProfileFactory(runtime),
        connector=connector,
    )

    source, masked = service.resolve_masked_migration_db_url()

    assert "MIGRATION_DATABASE_URL" == source
    assert "supersecret" not in masked
    assert "***" in masked


def test_assert_migration_create_privilege_returns_current_user_when_allowed():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )
    conn = connector.connection
    conn.cursor_instance.set_fetchone_result(("supabase_admin", True))

    current_user = service.assert_migration_create_privilege(conn)

    assert "supabase_admin" == current_user


def test_assert_migration_create_privilege_raises_when_not_allowed():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )
    conn = connector.connection
    conn.cursor_instance.set_fetchone_result(("postgres", False))

    with pytest.raises(PermissionError, match="does not have CREATE privilege"):
        service.assert_migration_create_privilege(conn)
