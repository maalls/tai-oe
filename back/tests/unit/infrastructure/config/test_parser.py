import pytest

from src.infrastructure.config.models import (
    DatabaseRuntimeHints,
    ResolvedRuntimeConfig,
    SharedSupabaseConfig,
)
from src.infrastructure.config.parser import (
    mask_connection_url,
    parse_database_runtime_hints,
    parse_shared_supabase_config,
)


def test_parse_shared_supabase_config_requires_postgres_password():
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        parse_shared_supabase_config({"POSTGRES_HOST": "localhost"})


def test_parse_shared_supabase_config_parses_optional_values():
    config = parse_shared_supabase_config(
        {
            "POSTGRES_PASSWORD": "pw",
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "6543",
            "POSTGRES_DB": "ge_prod",
            "SUPABASE_PUBLIC_URL": "https://supabase.example.com",
            "ANON_KEY": "anon",
            "SERVICE_ROLE_KEY": "service",
        }
    )

    assert isinstance(config, SharedSupabaseConfig)
    assert "pw" == config.postgres_password
    assert "db" == config.postgres_host
    assert 6543 == config.postgres_port
    assert "ge_prod" == config.postgres_db
    assert "https://supabase.example.com" == config.supabase_public_url
    assert "anon" == config.anon_key
    assert "service" == config.service_role_key


def test_parse_database_runtime_hints_extracts_from_database_url():
    hints = parse_database_runtime_hints(
        "postgresql://postgres.ge-prod:pw@localhost:5432/ge_prod?sslmode=require"
    )

    assert isinstance(hints, DatabaseRuntimeHints)
    assert "postgres.ge-prod" == hints.username
    assert "localhost" == hints.host
    assert 5432 == hints.port
    assert "ge_prod" == hints.database
    assert "require" == hints.sslmode
    assert "ge-prod" == hints.tenant_suffix


def test_parse_database_runtime_hints_defaults_when_url_missing_parts():
    hints = parse_database_runtime_hints("postgresql://user:pw@localhost/ge_prod")

    assert 5432 == hints.port
    assert "prefer" == hints.sslmode
    assert hints.tenant_suffix is None


def test_mask_connection_url_hides_password():
    masked = mask_connection_url("postgresql://user:secret@localhost:5432/ge_prod")
    assert "secret" not in masked
    assert "***" in masked


def test_resolved_runtime_config_is_immutable():
    shared = SharedSupabaseConfig(postgres_password="pw")
    hints = DatabaseRuntimeHints(
        host="localhost",
        port=5432,
        database="ge_prod",
        username="postgres",
        sslmode="prefer",
    )
    resolved = ResolvedRuntimeConfig(shared=shared, db_hints=hints)

    with pytest.raises(Exception):
        resolved.shared = shared
