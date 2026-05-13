"""Tests for VendorService.get_vendor."""

from domain.vendor import Vendor
from service.vendor.vendor_service import VendorService


class _VendorRepo:
    def __init__(self, vendor: Vendor):
        self.vendor = vendor

    def get_by_id(self, vendor_id: str) -> Vendor:
        return self.vendor

    def save(self, vendor: Vendor) -> None:
        self.vendor = vendor


def test_get_vendor_returns_entity():
    repo = _VendorRepo(Vendor(id="v-1", name="Vendor A"))
    service = VendorService(repo)

    result = service.get_vendor("v-1")

    assert result.name == "Vendor A"
