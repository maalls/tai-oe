"""Single-source runtime configuration provider."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

from dotenv import dotenv_values

from .models import DatabaseRuntimeHints, ResolvedRuntimeConfig
from .parser import parse_database_runtime_hints, parse_shared_supabase_config


class ConfigProvider:
    """Resolve runtime configuration from env + shared Supabase env file."""

    def __init__(
        self,
        environ: Optional[Mapping[str, str]] = None,
        env_file_path: Optional[Path] = None,
        current_file: Optional[str] = None,
    ) -> None:
        self._environ = dict(environ or {})
        self._env_file_path = Path(env_file_path).resolve() if env_file_path else None
        self._current_file = Path(current_file).resolve() if current_file else Path(__file__).resolve()

    def resolve(self) -> ResolvedRuntimeConfig:
        local_env_values = self._load_env_file_values(self._env_file_path)

        shared_env_rel = (
            self._environ.get("SUPABASE_ENV_FILE")
            or local_env_values.get("SUPABASE_ENV_FILE")
            or "../supabase/.env.prod"
        )
        shared_env_path = self._resolve_shared_env_path(shared_env_rel)
        shared_env_values = self._load_env_file_values(shared_env_path)

        shared = parse_shared_supabase_config(shared_env_values)

        supabase_url = (
            self._environ.get("SUPABASE_URL")
            or local_env_values.get("SUPABASE_URL")
            or shared.supabase_public_url
        )
        supabase_anon_key = (
            self._environ.get("SUPABASE_ANON_KEY")
            or local_env_values.get("SUPABASE_ANON_KEY")
            or shared.anon_key
        )
        supabase_service_key = (
            self._environ.get("SUPABASE_SERVICE_KEY")
            or local_env_values.get("SUPABASE_SERVICE_KEY")
            or shared.service_role_key
        )

        database_url = self._environ.get("DATABASE_URL") or local_env_values.get("DATABASE_URL")
        if database_url:
            db_hints = parse_database_runtime_hints(database_url)
        else:
            db_hints = DatabaseRuntimeHints(
                host=shared.postgres_host,
                port=shared.postgres_port,
                database=shared.postgres_db,
            )

        return ResolvedRuntimeConfig(
            shared=shared,
            db_hints=db_hints,
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_service_key=supabase_service_key,
        )

    def _resolve_shared_env_path(self, shared_env_rel: str) -> Path:
        path = Path(shared_env_rel)
        if path.is_absolute():
            return path

        if self._env_file_path:
            return (self._env_file_path.parent / path).resolve()

        base_dir = self._current_file.parents[3]
        return (base_dir / path).resolve()

    @staticmethod
    def _load_env_file_values(path: Optional[Path]) -> dict[str, str]:
        if not path or not path.exists():
            return {}

        values = dotenv_values(path)
        return {
            str(key): str(value)
            for key, value in values.items()
            if key and value is not None
        }
