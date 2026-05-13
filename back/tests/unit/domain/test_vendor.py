"""Tests for Vendor domain entity."""

from datetime import datetime, timezone

import pytest

from domain.vendor import Vendor


def test_vendor_creation():
    vendor = Vendor(
        id="v-1",
        name="Vendor One",
        email="sales@vendor.com",
        created_at=datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc),
    )

    assert vendor.id == "v-1"
    assert vendor.name == "Vendor One"
    assert vendor.email == "sales@vendor.com"
    assert vendor.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_vendor_is_immutable():
    vendor = Vendor(id="v-2", name="Vendor Two")

    with pytest.raises(Exception):
        vendor.name = "Changed"
