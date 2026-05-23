"""Single-source runtime configuration provider."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

from dotenv import dotenv_values

from .models import DatabaseRuntimeHints, ResolvedRuntimeConfig
from .parser import parse_shared_supabase_config


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
        merged_shared_values = self._merge_postgres_overrides(
            shared_env_values,
            local_env_values,
            self._environ,
        )

        shared = parse_shared_supabase_config(
            merged_shared_values,
            require_postgres_password=self._require_postgres_password,
        )

        self._validate_required_supabase_settings(shared_env_path, shared)

        # Single source of truth for Supabase runtime credentials:
        # values parsed from SUPABASE_ENV_FILE.
        supabase_url = shared.supabase_public_url
        supabase_anon_key = shared.anon_key
        supabase_service_key = shared.service_role_key

        db_hints = DatabaseRuntimeHints(
            host=shared.postgres_host,
            port=shared.postgres_port,
            database=shared.postgres_db,
            username=shared.postgres_user,
        )

        return ResolvedRuntimeConfig(
            shared=shared,
            db_hints=db_hints,
            database_url=None,
            migration_database_url=None,
            admin_database_url=None,
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_service_key=supabase_service_key,
        )

    @staticmethod
    def _validate_required_supabase_settings(shared_env_path: Path, shared) -> None:
        missing: list[str] = []

        if not shared.supabase_public_url:
            missing.append("SUPABASE_PUBLIC_URL (or API_EXTERNAL_URL / SITE_URL)")
        if not shared.anon_key:
            missing.append("ANON_KEY")
        if not shared.service_role_key:
            missing.append("SERVICE_ROLE_KEY")

        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(
                "Missing required Supabase settings in "
                f"{shared_env_path}: {missing_list}. "
                "Fix SUPABASE_ENV_FILE before starting the server."
            )

    @staticmethod
    def _merge_postgres_overrides(
        shared_values: Mapping[str, str],
        local_values: Mapping[str, str],
        environ: Mapping[str, str],
    ) -> dict[str, str]:
        """Merge POSTGRES_* values with precedence: process env > local env > shared env."""
        merged = dict(shared_values)
        postgres_keys = (
            "POSTGRES_PASSWORD",
            "POSTGRES_USER",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
        )
        for key in postgres_keys:
            value = environ.get(key) or local_values.get(key)
            if value:
                merged[key] = value
        return merged

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
