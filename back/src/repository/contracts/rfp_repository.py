"""RFP repository contract."""

from abc import ABC, abstractmethod

from src.domain.rfp import Rfp


class RfpRepositoryContract(ABC):
    """Abstract contract for RFP persistence."""

    @abstractmethod
    def get_by_id(self, rfp_id: str) -> Rfp:
        """Retrieve an RFP by id."""

    @abstractmethod
    def save(self, rfp: Rfp) -> None:
        """Persist an RFP."""
