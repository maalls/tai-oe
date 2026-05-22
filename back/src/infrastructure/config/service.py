"""Database connection service using explicit configuration profiles."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Optional
from urllib.parse import quote

import psycopg2

from .factory import DbProfileFactory


class DatabaseService:
    """Open DB connections/cursors using app or migration profiles."""

    def __init__(
        self,
        *,
        profile_factory: DbProfileFactory,
        connector: Optional[Callable[..., object]] = None,
    ) -> None:
        self._profile_factory = profile_factory
        self._connector = connector or psycopg2.connect

    def connect(
        self,
        *,
        profile_name: str = "app",
        migration_database_url: Optional[str] = None,
        admin_database_url: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        profile = self._resolve_profile(
            profile_name=profile_name,
            migration_database_url=migration_database_url,
            admin_database_url=admin_database_url,
            database_url=database_url,
        )

        return self._connector(
            host=profile.host,
            port=profile.port,
            database=profile.database,
            user=profile.user,
            password=profile.password,
            sslmode=profile.sslmode,
        )

    def create_migration_db(self):
        """Create a migration-scoped DB connection."""
        return self.connect(profile_name="migration")

    def resolve_migration_db_url(self) -> tuple[str, str]:
        """Resolve migration DB source and log-safe raw URL."""
        profile = self._resolve_profile(
            profile_name="migration",
            migration_database_url=None,
            admin_database_url=None,
            database_url=None,
        )

        if profile.source in ("MIGRATION_DATABASE_URL", "ADMIN_DATABASE_URL", "DATABASE_URL"):
            value = self._profile_factory.get_configured_database_url(profile.source)
            if value:
                return profile.source, value

        db_url = (
            f"postgresql://{profile.user}:{quote(profile.password, safe='')}"
            f"@{profile.host}:{profile.port}/{profile.database}"
        )
        return profile.source, db_url

    @contextmanager
    def cursor(
        self,
        *,
        profile_name: str = "app",
        migration_database_url: Optional[str] = None,
        admin_database_url: Optional[str] = None,
        database_url: Optional[str] = None,
    ):
        conn = self.connect(
            profile_name=profile_name,
            migration_database_url=migration_database_url,
            admin_database_url=admin_database_url,
            database_url=database_url,
        )
        cur = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()
            conn.close()

    def _resolve_profile(
        self,
        *,
        profile_name: str,
        migration_database_url: Optional[str],
        admin_database_url: Optional[str],
        database_url: Optional[str],
    ):
        if profile_name == "app":
            return self._profile_factory.build_app_profile()
        if profile_name == "migration":
            return self._profile_factory.build_migration_profile(
                migration_database_url=migration_database_url,
                admin_database_url=admin_database_url,
                database_url=database_url,
            )

        raise ValueError(f"Unsupported profile_name: {profile_name}")
