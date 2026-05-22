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
