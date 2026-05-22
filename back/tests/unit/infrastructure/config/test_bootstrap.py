from src.infrastructure.config.bootstrap import (
    create_database_service,
    create_db_profile_factory,
    create_runtime_config,
)
from src.infrastructure.config.factory import DbProfileFactory
from src.infrastructure.config.models import ResolvedRuntimeConfig


def test_create_database_service_returns_database_service_instance():
    service = create_database_service(current_file=__file__, require_postgres_password=False)
    assert service is not None
    assert service.__class__.__name__ == "DatabaseService"


def test_create_runtime_config_returns_resolved_runtime_config_instance():
    runtime_config = create_runtime_config(current_file=__file__, require_postgres_password=False)
    assert runtime_config is not None
    assert isinstance(runtime_config, ResolvedRuntimeConfig)


def test_create_db_profile_factory_returns_factory_instance():
    runtime_config = create_runtime_config(current_file=__file__, require_postgres_password=False)
    profile_factory = create_db_profile_factory(runtime_config)
    assert profile_factory is not None
    assert isinstance(profile_factory, DbProfileFactory)
