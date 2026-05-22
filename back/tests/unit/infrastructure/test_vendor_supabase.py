"""Tests for SupabaseVendorRepository."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.vendor_supabase import SupabaseVendorRepository
from domain.vendor import Vendor


def _mock_db_handler_with_data(data, update_rows_affected=1):
    db_handler = MagicMock()
    db_handler.execute_dict_query.return_value = data
    db_handler.execute_update.return_value = update_rows_affected
    return db_handler


def test_vendor_get_by_id_maps_domain():
    db_handler = _mock_db_handler_with_data([
        {
            "id": "v-1",
            "name": "Vendor A",
            "email": "a@vendor.com",
            "phone": None,
            "website": None,
            "created_at": "2026-05-13T10:20:30Z",
        }
    ])
    repo = SupabaseVendorRepository(db_handler=db_handler)

    vendor = repo.get_by_id("v-1")

    assert vendor.id == "v-1"
    assert vendor.name == "Vendor A"
    assert vendor.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_vendor_get_by_id_not_found():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseVendorRepository(db_handler=db_handler)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_vendor_save_updates_payload():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseVendorRepository(db_handler=db_handler)
    vendor = Vendor(id="v-save", name="Vendor Save", email="save@vendor.com")

    repo.save(vendor)

    params = db_handler.execute_update.call_args.args[1]
    assert params[0] == "Vendor Save"
    assert params[1] == "save@vendor.com"
