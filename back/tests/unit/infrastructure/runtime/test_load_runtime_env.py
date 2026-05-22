import os
from pathlib import Path

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
