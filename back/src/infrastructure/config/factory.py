"""Factory for deriving DB connection profiles from resolved runtime config."""

from __future__ import annotations

from typing import Optional

from .models import DbProfile, ResolvedRuntimeConfig
from .parser import parse_database_runtime_hints


class DbProfileFactory:
    """Builds explicit app/migration DB profiles from a single resolved config."""

    def __init__(self, runtime_config: ResolvedRuntimeConfig):
        self._config = runtime_config

    def build_app_profile(self) -> DbProfile:
        hints = self._config.db_hints
        return DbProfile(
            host=hints.host,
            port=hints.port,
            database=hints.database,
            user=hints.username or "postgres",
            password=self._config.shared.postgres_password,
            sslmode=hints.sslmode,
            source="app-hints",
        )

    def build_migration_profile(
        self,
        *,
        migration_database_url: Optional[str],
        admin_database_url: Optional[str],
        database_url: Optional[str],
    ) -> DbProfile:
        if migration_database_url:
            return self._profile_from_url(migration_database_url, source="MIGRATION_DATABASE_URL")

        if admin_database_url:
            return self._profile_from_url(admin_database_url, source="ADMIN_DATABASE_URL")

        runtime_hints = parse_database_runtime_hints(database_url) if database_url else self._config.db_hints

        if not self._config.shared.postgres_password and database_url:
            return self._profile_from_url(database_url, source="DATABASE_URL")

        tenant_suffix = runtime_hints.tenant_suffix
        migration_user = f"supabase_admin.{tenant_suffix}" if tenant_suffix else "supabase_admin"

        return DbProfile(
            host=runtime_hints.host,
            port=runtime_hints.port,
            database=runtime_hints.database,
            user=migration_user,
            password=self._config.shared.postgres_password,
            sslmode=runtime_hints.sslmode,
            source="SUPABASE_ENV_FILE",
        )

    @staticmethod
    def _profile_from_url(db_url: str, *, source: str) -> DbProfile:
        hints = parse_database_runtime_hints(db_url)
        return DbProfile(
            host=hints.host,
            port=hints.port,
            database=hints.database,
            user=hints.username or "postgres",
            password="" if source == "derived" else _password_from_url(db_url),
            sslmode=hints.sslmode,
            source=source,
        )


def _password_from_url(db_url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(db_url).password or ""
