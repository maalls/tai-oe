"""Runtime environment bootstrap for API server startup."""

import os
from pathlib import Path


def load_runtime_env(current_file: str) -> None:
    """Load local and shared environment variables used by the API server."""
    try:
        from dotenv import dotenv_values, find_dotenv, load_dotenv

        env_file = find_dotenv(usecwd=True)
        if env_file:
            load_dotenv(env_file, override=False)
            print(f"[dotenv] Loaded from {env_file}")

        # Optional: load shared Supabase env (single source of truth)
        shared_env_rel = os.environ.get("SUPABASE_ENV_FILE", "../supabase/.env.prod")
        shared_env_path = Path(shared_env_rel)
        if not shared_env_path.is_absolute():
            base_dir = Path(env_file).parent if env_file else Path(current_file).resolve().parents[2]
            shared_env_path = (base_dir / shared_env_rel).resolve()

        if shared_env_path.exists():
            shared_env = dotenv_values(shared_env_path)
            os.environ["SUPABASE_URL"] = (
                shared_env.get("SUPABASE_PUBLIC_URL")
                or shared_env.get("API_EXTERNAL_URL")
                or shared_env.get("SITE_URL")
                or os.environ.get("SUPABASE_URL", "")
            )
            os.environ["SUPABASE_ANON_KEY"] = (
                shared_env.get("ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
            )
            os.environ["SUPABASE_SERVICE_KEY"] = (
                shared_env.get("SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY", "")
            )
    except Exception:
        # Startup should not fail if dotenv is unavailable or env files are missing.
        pass
