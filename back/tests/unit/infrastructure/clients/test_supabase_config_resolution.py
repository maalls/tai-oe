from src.infrastructure.clients.supabase import _resolve_supabase_credentials


def test_resolve_supabase_credentials_prefers_process_env(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "SUPABASE_PUBLIC_URL=https://shared.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    supabase_url, anon_key, service_key = _resolve_supabase_credentials(
        environ={
            "SUPABASE_URL": "https://process.example.com",
            "SUPABASE_ANON_KEY": "process-anon",
            "SUPABASE_SERVICE_KEY": "process-service",
        },
        env_file_path=env_file,
    )

    assert "https://process.example.com" == supabase_url
    assert "process-anon" == anon_key
    assert "process-service" == service_key


def test_resolve_supabase_credentials_falls_back_to_shared_env(tmp_path):
    env_file = tmp_path / "back.env"
    shared_env = tmp_path / ".env.prod"

    env_file.write_text(f"SUPABASE_ENV_FILE={shared_env}\n", encoding="utf-8")
    shared_env.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=shared_pw",
                "API_EXTERNAL_URL=https://api.example.com",
                "ANON_KEY=shared-anon",
                "SERVICE_ROLE_KEY=shared-service",
            ]
        ),
        encoding="utf-8",
    )

    supabase_url, anon_key, service_key = _resolve_supabase_credentials(
        environ={},
        env_file_path=env_file,
    )

    assert "https://api.example.com" == supabase_url
    assert "shared-anon" == anon_key
    assert "shared-service" == service_key
