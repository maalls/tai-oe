"""Tests for SupabaseRfpRepository."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.enums import DocumentStatus
from domain.rfp import Rfp
from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.rfp_supabase import SupabaseRfpRepository


def _mock_supabase_with_data(data):
    supabase = MagicMock()
    query = supabase.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.limit.return_value = query
    query.execute.return_value = MagicMock(data=data)
    return supabase


def test_rfp_get_by_id_maps_domain():
    supabase = _mock_supabase_with_data([
        {
            "id": "r-1",
            "type": "RFP",
            "title": "RFP A",
            "status": "DRAFT",
            "created_at": "2026-05-13T10:20:30Z",
        }
    ])
    repo = SupabaseRfpRepository(supabase)

    rfp = repo.get_by_id("r-1")

    assert rfp.id == "r-1"
    assert rfp.title == "RFP A"
    assert rfp.status == DocumentStatus.DRAFT
    assert rfp.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_rfp_get_by_id_not_found():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseRfpRepository(supabase)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_rfp_save_updates_payload():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseRfpRepository(supabase)
    rfp = Rfp(id="r-save", title="RFP Save", requester_email=None, content=None, status=DocumentStatus.SUBMITTED)

    repo.save(rfp)

    payload = supabase.table.return_value.update.call_args.args[0]
    assert payload["type"] == "RFP"
    assert payload["status"] == "SUBMITTED"
