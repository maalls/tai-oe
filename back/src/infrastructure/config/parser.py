"""Parsing utilities for typed runtime configuration."""

from typing import Mapping, Optional
from urllib.parse import parse_qs, urlparse

from .models import DatabaseRuntimeHints, SharedSupabaseConfig


def _parse_int(raw_value: Optional[str], *, key: str, default: int) -> int:
    if raw_value in (None, ""):
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {key}: {raw_value}") from exc


def parse_shared_supabase_config(
    values: Mapping[str, str],
    *,
    require_postgres_password: bool = True,
) -> SharedSupabaseConfig:
    """Parse and validate shared Supabase environment values."""
    postgres_password = values.get("POSTGRES_PASSWORD")
    if require_postgres_password and not postgres_password:
        raise ValueError("Missing required key POSTGRES_PASSWORD in shared Supabase env")

    supabase_public_url = (
        values.get("SUPABASE_PUBLIC_URL")
        or values.get("API_EXTERNAL_URL")
        or values.get("SITE_URL")
    )

    return SharedSupabaseConfig(
        postgres_password=postgres_password or "",
        postgres_user=values.get("POSTGRES_USER", "postgres"),
        postgres_host=values.get("POSTGRES_HOST", "localhost"),
        postgres_port=_parse_int(values.get("POSTGRES_PORT"), key="POSTGRES_PORT", default=5432),
        postgres_db=values.get("POSTGRES_DB", "postgres"),
        supabase_public_url=supabase_public_url,
        anon_key=values.get("ANON_KEY"),
        service_role_key=values.get("SERVICE_ROLE_KEY"),
    )


def parse_database_runtime_hints(database_url: str) -> DatabaseRuntimeHints:
    """Extract normalized database connection hints from DATABASE_URL."""
    parsed = urlparse(database_url)
    if not parsed.scheme:
        raise ValueError(f"Invalid DATABASE_URL: {database_url}")

    query = parse_qs(parsed.query)
    username = parsed.username
    tenant_suffix = username.split(".", 1)[1] if username and "." in username else None

    return DatabaseRuntimeHints(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=(parsed.path or "").lstrip("/") or "postgres",
        username=username,
        sslmode=query.get("sslmode", ["prefer"])[0],
        tenant_suffix=tenant_suffix,
    )


def mask_connection_url(database_url: str) -> str:
    """Return a log-safe connection URL with hidden password."""
    parsed = urlparse(database_url)
    if not parsed.scheme:
        return "<invalid database url>"

    auth = parsed.username or "<unknown-user>"
    if parsed.password:
        auth = f"{auth}:***"

    host = parsed.hostname or "<unknown-host>"
    port = parsed.port or 5432
    database = (parsed.path or "").lstrip("/") or "postgres"
    return f"{parsed.scheme}://{auth}@{host}:{port}/{database}"
