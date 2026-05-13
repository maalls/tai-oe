"""Tests for SupabaseVendorRepository."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.vendor_supabase import SupabaseVendorRepository
from domain.vendor import Vendor


def _mock_supabase_with_data(data):
    supabase = MagicMock()
    query = supabase.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.limit.return_value = query
    query.execute.return_value = MagicMock(data=data)
    return supabase


def test_vendor_get_by_id_maps_domain():
    supabase = _mock_supabase_with_data([
        {
            "id": "v-1",
            "name": "Vendor A",
            "email": "a@vendor.com",
            "phone": None,
            "website": None,
            "created_at": "2026-05-13T10:20:30Z",
        }
    ])
    repo = SupabaseVendorRepository(supabase)

    vendor = repo.get_by_id("v-1")

    assert vendor.id == "v-1"
    assert vendor.name == "Vendor A"
    assert vendor.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_vendor_get_by_id_not_found():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseVendorRepository(supabase)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_vendor_save_updates_payload():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseVendorRepository(supabase)
    vendor = Vendor(id="v-save", name="Vendor Save", email="save@vendor.com")

    repo.save(vendor)

    payload = supabase.table.return_value.update.call_args.args[0]
    assert payload["name"] == "Vendor Save"
    assert payload["email"] == "save@vendor.com"
