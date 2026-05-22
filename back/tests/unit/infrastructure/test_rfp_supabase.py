"""Tests for SupabaseRfpRepository."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.enums import DocumentStatus
from domain.rfp import Rfp
from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.rfp_supabase import SupabaseRfpRepository


def _mock_db_handler_with_data(data, update_rows_affected=1):
    db_handler = MagicMock()
    db_handler.execute_dict_query.return_value = data
    db_handler.execute_update.return_value = update_rows_affected
    return db_handler


def test_rfp_get_by_id_maps_domain():
    db_handler = _mock_db_handler_with_data([
        {
            "id": "r-1",
            "type": "RFP",
            "title": "RFP A",
            "status": "DRAFT",
            "created_at": "2026-05-13T10:20:30Z",
        }
    ])
    repo = SupabaseRfpRepository(db_handler=db_handler)

    rfp = repo.get_by_id("r-1")

    assert rfp.id == "r-1"
    assert rfp.title == "RFP A"
    assert rfp.status == DocumentStatus.DRAFT
    assert rfp.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_rfp_get_by_id_not_found():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseRfpRepository(db_handler=db_handler)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_rfp_save_updates_payload():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseRfpRepository(db_handler=db_handler)
    rfp = Rfp(id="r-save", title="RFP Save", requester_email=None, content=None, status=DocumentStatus.SUBMITTED)

    repo.save(rfp)

    params = db_handler.execute_update.call_args.args[1]
    assert params[0] == "RFP"
    assert params[2] == "SUBMITTED"
