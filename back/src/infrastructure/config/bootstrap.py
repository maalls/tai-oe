"""High-level constructors for config-backed infrastructure services."""

from __future__ import annotations

import os
from pathlib import Path

from .factory import DbProfileFactory
from .provider import ConfigProvider
from .service import DatabaseService


def create_database_service(*, current_file: str, require_postgres_password: bool = False) -> DatabaseService:
    """Create a DatabaseService from process environment + shared env configuration."""
    runtime_config = ConfigProvider(
        environ=os.environ,
        env_file_path=None,
        current_file=current_file,
        require_postgres_password=require_postgres_password,
    ).resolve()
    return DatabaseService(profile_factory=DbProfileFactory(runtime_config))
