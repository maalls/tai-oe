"""Supabase client wrapper for authentication and database operations."""

import os
import httpx
from pathlib import Path
from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
from dotenv import find_dotenv
from src.infrastructure.config.provider import ConfigProvider


def _resolve_supabase_credentials(
    *,
    environ: dict[str, str] | None = None,
    env_file_path: Path | None = None,
):
    """Resolve Supabase URL and keys via the shared ConfigProvider pipeline."""
    effective_env = dict(os.environ) if environ is None else dict(environ)

    effective_env_file = env_file_path
    if effective_env_file is None:
        discovered_env = find_dotenv(usecwd=True)
        effective_env_file = Path(discovered_env) if discovered_env else None

    runtime_config = ConfigProvider(
        environ=effective_env,
        env_file_path=effective_env_file,
        current_file=str(Path(__file__).resolve()),
        require_postgres_password=False,
    ).resolve()

    return (
        runtime_config.supabase_url,
        runtime_config.supabase_anon_key,
        runtime_config.supabase_service_key,
    )

_supabase_anon: Client = None
_supabase_service: Client = None
_supabase_httpx_client: httpx.Client = None


def _get_supabase_httpx_client() -> httpx.Client:
    global _supabase_httpx_client
    if _supabase_httpx_client is None:
        _supabase_httpx_client = httpx.Client(timeout=120.0)
    return _supabase_httpx_client


def _get_supabase_options() -> SyncClientOptions:
    return SyncClientOptions(httpx_client=_get_supabase_httpx_client())


def get_supabase_anon() -> Client:
    """Get the Supabase anon client (respects Row Level Security)."""
    global _supabase_anon
    if _supabase_anon is None:
        supabase_url, supabase_anon_key, _ = _resolve_supabase_credentials()
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        _supabase_anon = create_client(supabase_url, supabase_anon_key, options=_get_supabase_options())
    return _supabase_anon


def get_supabase_service() -> Client:
    """Get the Supabase service-role client (bypasses Row Level Security)."""
    global _supabase_service
    if _supabase_service is None:
        supabase_url, _, supabase_service_key = _resolve_supabase_credentials()
        if not supabase_url or not supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        _supabase_service = create_client(supabase_url, supabase_service_key, options=_get_supabase_options())
    return _supabase_service


__all__ = ["get_supabase_anon", "get_supabase_service"]
