"""High-level constructors for config-backed infrastructure services."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv

from .factory import DbProfileFactory
from .provider import ConfigProvider
from .service import DatabaseService


def create_database_service(*, current_file: str, require_postgres_password: bool = False) -> DatabaseService:
    """Create a DatabaseService from process environment + shared env configuration."""
    discovered_env = find_dotenv(usecwd=True)
    env_file_path = Path(discovered_env).resolve() if discovered_env else None
    runtime_config = ConfigProvider(
        environ=os.environ,
        env_file_path=env_file_path,
        current_file=current_file,
        require_postgres_password=require_postgres_password,
    ).resolve()
    return DatabaseService(profile_factory=DbProfileFactory(runtime_config))
