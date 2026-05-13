"""Vendor repository contract."""

from abc import ABC, abstractmethod

from src.domain.vendor import Vendor


class VendorRepositoryContract(ABC):
    """Abstract contract for vendor persistence."""

    @abstractmethod
    def get_by_id(self, vendor_id: str) -> Vendor:
        """Retrieve a vendor by id."""

    @abstractmethod
    def save(self, vendor: Vendor) -> None:
        """Persist a vendor."""
