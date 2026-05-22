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
        require_postgres_password: bool = True,
    ) -> None:
        self._environ = dict(environ or {})
        self._env_file_path = Path(env_file_path).resolve() if env_file_path else None
        self._current_file = Path(current_file).resolve() if current_file else Path(__file__).resolve()
        self._require_postgres_password = require_postgres_password

    def resolve(self) -> ResolvedRuntimeConfig:
        local_env_values = self._load_env_file_values(self._env_file_path)

        shared_env_rel = (
            self._environ.get("SUPABASE_ENV_FILE")
            or local_env_values.get("SUPABASE_ENV_FILE")
            or "../supabase/.env.prod"
        )
        shared_env_path = self._resolve_shared_env_path(shared_env_rel)
        shared_env_values = self._load_env_file_values(shared_env_path)

        shared = parse_shared_supabase_config(
            shared_env_values,
            require_postgres_password=self._require_postgres_password,
        )

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

        migration_database_url = (
            self._environ.get("MIGRATION_DATABASE_URL")
            or local_env_values.get("MIGRATION_DATABASE_URL")
        )
        admin_database_url = (
            self._environ.get("ADMIN_DATABASE_URL")
            or local_env_values.get("ADMIN_DATABASE_URL")
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
            database_url=database_url,
            migration_database_url=migration_database_url,
            admin_database_url=admin_database_url,
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

        base_dir = self._infer_backend_dir(self._current_file)
        return (base_dir / path).resolve()

    @staticmethod
    def _infer_backend_dir(current_file: Path) -> Path:
        for ancestor in [current_file, *current_file.parents]:
            if ancestor.is_dir() and ancestor.name == "back":
                return ancestor
            if ancestor.is_file() and ancestor.parent.name == "back":
                return ancestor.parent

        if len(current_file.parents) >= 4:
            return current_file.parents[3]
        return current_file.parent

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
