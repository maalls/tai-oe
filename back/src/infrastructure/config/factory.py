"""Factory for deriving DB connection profiles from resolved runtime config."""

from __future__ import annotations

from typing import Optional

from .models import DbProfile, ResolvedRuntimeConfig


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
            user=hints.username or self._config.shared.postgres_user,
            password=self._config.shared.postgres_password,
            sslmode=hints.sslmode,
            source="SUPABASE_ENV_FILE",
        )

    def build_migration_profile(
        self,
        *,
        migration_database_url=None,
        admin_database_url=None,
        database_url=None,
    ) -> DbProfile:
        del migration_database_url, admin_database_url, database_url
        return self.build_app_profile()

    def get_configured_database_url(self, source: str) -> Optional[str]:
        """Return configured raw URL value for explicit DB URL sources."""
        del source
        return None
