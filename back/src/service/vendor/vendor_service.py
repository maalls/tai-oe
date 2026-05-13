"""Application service for vendor operations."""

from src.domain.vendor import Vendor
from src.repository.contracts.vendor_repository import VendorRepositoryContract


class VendorService:
    """Service orchestrating vendor operations."""

    def __init__(self, repository: VendorRepositoryContract):
        self.repo = repository

    def get_vendor(self, vendor_id: str) -> Vendor:
        return self.repo.get_by_id(vendor_id)

    def save_vendor(self, vendor: Vendor) -> None:
        self.repo.save(vendor)
