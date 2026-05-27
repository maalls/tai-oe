"""High-level constructors for config-backed infrastructure services."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional

from dotenv import find_dotenv, dotenv_values

from .factory import DbProfileFactory
from .models import ResolvedRuntimeConfig
from .provider import ConfigProvider
from .service import DatabaseService


def create_runtime_config(
    *,
    current_file: str,
    require_postgres_password: bool = False,
    environ: Optional[Mapping[str, str]] = None,
    env_file_path: Optional[Path] = None,
) -> ResolvedRuntimeConfig:
    """Resolve and return normalized runtime configuration."""
    effective_environ = dict(os.environ) if environ is None else dict(environ)

    effective_env_file_path = env_file_path
    if effective_env_file_path is None:
        discovered_env = find_dotenv(usecwd=True)
        effective_env_file_path = Path(discovered_env).resolve() if discovered_env else None

    # Keep process env as priority, but fill missing keys from discovered .env
    # so CLI entrypoints (e.g. migrations) behave like dev_server startup.
    if effective_env_file_path and effective_env_file_path.exists():
        file_values = dotenv_values(effective_env_file_path)
        for key, value in file_values.items():
            if key and value is not None and key not in effective_environ:
                effective_environ[key] = str(value)

    return ConfigProvider(
        environ=effective_environ,
        env_file_path=effective_env_file_path,
        current_file=current_file,
        require_postgres_password=require_postgres_password,
    ).resolve()


def create_db_profile_factory(runtime_config: ResolvedRuntimeConfig) -> DbProfileFactory:
    """Create a DB profile factory from resolved runtime configuration."""
    return DbProfileFactory(runtime_config)


def create_database_service(*, current_file: str, require_postgres_password: bool = False) -> DatabaseService:
    """Create a DatabaseService from process environment + shared env configuration."""
    runtime_config = create_runtime_config(
        current_file=current_file,
        require_postgres_password=require_postgres_password,
    )
    return DatabaseService(profile_factory=create_db_profile_factory(runtime_config))


def create_database_handler(*, current_file: str, require_postgres_password: bool = False):
    """Create a DatabaseHandler from process environment + shared env configuration."""
    from src.infrastructure.clients.database import DatabaseHandler

    return DatabaseHandler(
        database_service=create_database_service(
            current_file=current_file,
            require_postgres_password=require_postgres_password,
        )
    )
