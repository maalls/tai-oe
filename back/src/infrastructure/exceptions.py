"""Infrastructure exceptions for repository and provider failures."""


class RepositoryError(Exception):
    """Raised when a repository operation fails."""


class NotFoundError(RepositoryError):
    """Raised when an entity is not found."""


class MappingError(RepositoryError):
    """Raised when DTO/domain mapping fails."""
