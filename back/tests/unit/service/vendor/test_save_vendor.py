"""Tests for VendorService.save_vendor."""

from domain.vendor import Vendor
from service.vendor.vendor_service import VendorService


class _VendorRepo:
    def __init__(self, vendor: Vendor | None = None):
        self.vendor = vendor
        self.saved_vendor = None

    def get_by_id(self, vendor_id: str) -> Vendor:
        return self.vendor

    def save(self, vendor: Vendor) -> None:
        self.saved_vendor = vendor


def test_save_vendor_persists_vendor():
    vendor = Vendor(id="v-1", name="Vendor A", email="a@vendor.com")
    repo = _VendorRepo()
    service = VendorService(repo)

    service.save_vendor(vendor)

    assert repo.saved_vendor is vendor
