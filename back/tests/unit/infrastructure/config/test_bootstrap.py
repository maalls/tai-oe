from src.infrastructure.config.bootstrap import create_database_service


def test_create_database_service_returns_database_service_instance():
    service = create_database_service(current_file=__file__, require_postgres_password=False)
    assert service is not None
    assert service.__class__.__name__ == "DatabaseService"
