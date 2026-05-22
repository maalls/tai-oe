"""Database repository composed from dedicated domain repository modules."""

from src.repository.database.core_repository import CoreDatabaseRepository
from src.repository.database.profile_repository import ProfileRepositoryMixin
from src.repository.database.schema_repository import SchemaRepositoryMixin


class DatabaseRepository(ProfileRepositoryMixin, SchemaRepositoryMixin, CoreDatabaseRepository):
    """Facade repository composed from profile/schema/core concerns."""

    pass

