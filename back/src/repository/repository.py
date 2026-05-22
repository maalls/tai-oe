"""Database repository composed from dedicated domain repository modules."""

from src.repository.core_repository import CoreDatabaseRepository
from src.repository.profile_repository import ProfileRepositoryMixin
from src.repository.schema_repository import SchemaRepositoryMixin


class DatabaseRepository(ProfileRepositoryMixin, SchemaRepositoryMixin, CoreDatabaseRepository):
    """Facade repository composed from profile/schema/core concerns."""

    pass

