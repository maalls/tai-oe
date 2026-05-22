"""High-level constructors for config-backed infrastructure services."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv

from .factory import DbProfileFactory
from .models import ResolvedRuntimeConfig
from .provider import ConfigProvider
from .service import DatabaseService


def create_runtime_config(*, current_file: str, require_postgres_password: bool = False) -> ResolvedRuntimeConfig:
    """Resolve and return normalized runtime configuration."""
    discovered_env = find_dotenv(usecwd=True)
    env_file_path = Path(discovered_env).resolve() if discovered_env else None
    return ConfigProvider(
        environ=os.environ,
        env_file_path=env_file_path,
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
