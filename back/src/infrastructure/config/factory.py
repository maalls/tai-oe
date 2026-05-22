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
        migration_database_url: Optional[str] = None,
        admin_database_url: Optional[str] = None,
        database_url: Optional[str] = None,
    ) -> DbProfile:
        migration_database_url = migration_database_url or self._config.migration_database_url
        admin_database_url = admin_database_url or self._config.admin_database_url
        database_url = database_url or self._config.database_url

        if migration_database_url:
            return self._profile_from_url(migration_database_url, source="MIGRATION_DATABASE_URL")

        if admin_database_url:
            return self._profile_from_url(admin_database_url, source="ADMIN_DATABASE_URL")

        if not self._config.shared.postgres_password:
            if database_url:
                return self._profile_from_url(database_url, source="DATABASE_URL")
            raise ValueError(
                "No PostgreSQL URL configured for migrations. "
                "Set MIGRATION_DATABASE_URL, ADMIN_DATABASE_URL, DATABASE_URL, "
                "or SUPABASE_ENV_FILE with POSTGRES_PASSWORD."
            )

        runtime_hints = parse_database_runtime_hints(database_url) if database_url else self._config.db_hints

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

    def get_configured_database_url(self, source: str) -> Optional[str]:
        """Return configured raw URL value for explicit DB URL sources."""
        source_map = {
            "MIGRATION_DATABASE_URL": self._config.migration_database_url,
            "ADMIN_DATABASE_URL": self._config.admin_database_url,
            "DATABASE_URL": self._config.database_url,
        }
        return source_map.get(source)

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
