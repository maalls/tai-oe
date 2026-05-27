"""Database repository composed from dedicated domain repository modules."""

from src.repository.profile_repository import ProfileRepository
from src.repository.schema_repository import SchemaRepository


class DatabaseRepository(ProfileRepository, SchemaRepository):
    """Facade repository composed from profile/schema/core concerns."""

    pass

