"""Opportunity repository contract."""

from abc import ABC, abstractmethod
from typing import List

from src.domain.opportunity import Opportunity


class OpportunityRepositoryContract(ABC):
    """Abstract contract for opportunity persistence."""

    @abstractmethod
    def get_by_id(self, opportunity_id: str) -> Opportunity:
        """Retrieve an opportunity by id."""

    @abstractmethod
    def save(self, opportunity: Opportunity) -> None:
        """Persist an opportunity."""

    @abstractmethod
    def get_open_by_user(self, user_id: str, limit: int = 100) -> List[Opportunity]:
        """Retrieve open opportunities for a user."""
