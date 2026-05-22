import pytest

from src.infrastructure.clients.database import DatabaseHandler


def test_database_handler_requires_database_service():
    with pytest.raises(ValueError, match="requires an injected database_service"):
        DatabaseHandler(config={"supabase": {"db": {}}})
