"""Runtime environment bootstrap for API server startup."""

import os
from pathlib import Path

from dotenv import find_dotenv

from src.infrastructure.config.provider import ConfigProvider


def load_runtime_env(current_file: str) -> None:
    """Warm up unified runtime config resolution without mutating process env."""
    try:
        env_file = find_dotenv(usecwd=True)
        env_file_path = Path(env_file).resolve() if env_file else None
        ConfigProvider(
            environ=os.environ,
            env_file_path=env_file_path,
            current_file=current_file,
            require_postgres_password=False,
        ).resolve()
    except Exception:
        # Startup should not fail when config files are missing.
        pass
