"""Email repository contract for the new domain architecture."""

from abc import ABC, abstractmethod
from typing import List

from domain.email import Email


class EmailRepositoryContract(ABC):
    """Abstract contract for Email persistence in the new architecture."""

    @abstractmethod
    def get_by_id(self, email_id: str) -> Email:
        """Retrieve an email by id."""

    @abstractmethod
    def get_all_unclassified(self, limit: int = 100, user_id: str | None = None) -> List[Email]:
        """Retrieve unclassified emails, optionally scoped by user id."""

    @abstractmethod
    def save(self, email: Email) -> None:
        """Persist an email."""

    @abstractmethod
    def save_many(self, emails: List[Email]) -> None:
        """Persist many emails in batch."""
