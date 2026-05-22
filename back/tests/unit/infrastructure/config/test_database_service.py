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
            postgres_user="app_user",
            postgres_host="shared-db",
            postgres_port=5432,
            postgres_db="ge_prod",
        ),
        db_hints=DatabaseRuntimeHints(
            host="runtime-db",
            port=5433,
            database="runtime",
            username="app_user",
            sslmode="require",
            tenant_suffix=None,
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
    kwargs = connector.calls[0]
    assert "runtime-db" == kwargs["host"]
    assert 5433 == kwargs["port"]
    assert "runtime" == kwargs["database"]
    assert "app_user" == kwargs["user"]
    assert "shared_pw" == kwargs["password"]
    assert "require" == kwargs["sslmode"]


def test_create_migration_db_uses_same_profile_as_app():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    app_conn = service.connect(profile_name="app")
    migration_conn = service.create_migration_db()

    assert app_conn is connector.connection
    assert migration_conn is connector.connection
    assert connector.calls[0] == connector.calls[1]


def test_resolve_migration_db_url_derives_from_unified_profile():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    source, db_url = service.resolve_migration_db_url()

    assert "SUPABASE_ENV_FILE" == source
    assert db_url.startswith("postgresql://app_user:shared_pw@runtime-db:5433/runtime")


def test_resolve_masked_migration_db_url_masks_password():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )

    source, masked = service.resolve_masked_migration_db_url()

    assert "SUPABASE_ENV_FILE" == source
    assert "shared_pw" not in masked
    assert "***" in masked


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


def test_assert_migration_create_privilege_returns_current_user_when_allowed():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )
    conn = connector.connection
    conn.cursor_instance.set_fetchone_result(("app_user", True))

    current_user = service.assert_migration_create_privilege(conn)

    assert "app_user" == current_user


def test_assert_migration_create_privilege_raises_when_not_allowed():
    connector = RecordingConnector()
    service = DatabaseService(
        profile_factory=DbProfileFactory(_runtime_config()),
        connector=connector,
    )
    conn = connector.connection
    conn.cursor_instance.set_fetchone_result(("app_user", False))

    with pytest.raises(PermissionError, match="does not have CREATE privilege"):
        service.assert_migration_create_privilege(conn)
