"""Typed configuration models for runtime configuration resolution."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote


@dataclass(frozen=True)
class SharedSupabaseConfig:
    """Shared Supabase environment values loaded from SUPABASE_ENV_FILE."""

    postgres_password: str
    postgres_user: str = "postgres"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"
    supabase_public_url: Optional[str] = None
    anon_key: Optional[str] = None
    service_role_key: Optional[str] = None


@dataclass(frozen=True)
class DatabaseRuntimeHints:
    """Resolved database connection hints derived from shared runtime config."""

    host: str
    port: int
    database: str
    username: Optional[str] = None
    sslmode: str = "prefer"
    tenant_suffix: Optional[str] = None


@dataclass(frozen=True)
class ResolvedRuntimeConfig:
    """Normalized runtime config assembled from shared and runtime sources."""

    shared: SharedSupabaseConfig
    db_hints: DatabaseRuntimeHints
    database_url: Optional[str] = None
    migration_database_url: Optional[str] = None
    admin_database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None


@dataclass(frozen=True)
class DbProfile:
    """Concrete PostgreSQL connection profile used by DB services/commands."""

    host: str
    port: int
    database: str
    user: str
    password: str
    sslmode: str = "prefer"
    source: str = "derived"

    def to_url(self) -> str:
        """Render profile as a PostgreSQL URL with safe password quoting."""
        encoded_password = quote(self.password, safe="")
        return (
            f"postgresql://{self.user}:{encoded_password}"
            f"@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"
        )
