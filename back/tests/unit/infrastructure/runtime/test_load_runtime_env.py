import os
from pathlib import Path

from src.infrastructure.runtime import env_loader
from src.infrastructure.runtime.env_loader import load_runtime_env


def test_load_runtime_env_applies_shared_supabase_values(tmp_path, monkeypatch):
    shared_env_file = tmp_path / ".env.prod"
    shared_env_file.write_text(
        "\n".join(
            [
                "SUPABASE_PUBLIC_URL=https://example.supabase.co",
                "ANON_KEY=anon-key",
                "SERVICE_ROLE_KEY=service-key",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("SUPABASE_ENV_FILE", str(shared_env_file))
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)

    load_runtime_env(current_file=str(Path(__file__)))

    assert os.environ.get("SUPABASE_URL") is None
    assert os.environ.get("SUPABASE_ANON_KEY") is None
    assert os.environ.get("SUPABASE_SERVICE_KEY") is None

def test_load_runtime_env_loads_dotenv_into_process_environ(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    shared_env = tmp_path / "shared.env"
    env_file.write_text(
        "\n".join(
            [
                f"SUPABASE_ENV_FILE={shared_env}",
                "LLM_MODEL=qwen/qwen2.5-vl-7b",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shared_env.write_text("POSTGRES_PASSWORD=secret\n", encoding="utf-8")

    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setattr(env_loader, "find_dotenv", lambda usecwd=True: str(env_file))

    env_loader.load_runtime_env(current_file=str(Path(__file__)))

    assert "qwen/qwen2.5-vl-7b" == os.environ.get("LLM_MODEL")
