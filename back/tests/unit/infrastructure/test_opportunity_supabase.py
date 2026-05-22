"""Tests for SupabaseOpportunityRepository."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.enums import OpportunityStage, OpportunityStatus
from domain.opportunity import Opportunity
from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.opportunity_supabase import SupabaseOpportunityRepository


def _mock_db_handler_with_data(data, update_rows_affected=1):
    db_handler = MagicMock()
    db_handler.execute_dict_query.return_value = data
    db_handler.execute_update.return_value = update_rows_affected
    return db_handler


def test_opportunity_get_by_id_maps_domain():
    db_handler = _mock_db_handler_with_data([
        {
            "id": "o-1",
            "owner_user_id": "u-1",
            "account_id": "a-1",
            "name": "Deal A",
            "stage": "NEGOTIATION",
            "status": "OPEN",
            "amount_estimated": 1000,
            "probability": 60,
            "expected_close_date": "2026-06-01",
            "source": "email",
            "source_reference_id": None,
            "created_at": "2026-05-13T10:20:30Z",
        }
    ])
    repo = SupabaseOpportunityRepository(db_handler=db_handler)

    opp = repo.get_by_id("o-1")

    assert opp.id == "o-1"
    assert opp.stage == OpportunityStage.NEGOTIATION
    assert opp.status == OpportunityStatus.OPEN
    assert opp.expected_close_date == date(2026, 6, 1)
    assert opp.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_opportunity_get_by_id_not_found():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseOpportunityRepository(db_handler=db_handler)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_opportunity_save_updates_payload():
    db_handler = _mock_db_handler_with_data([])
    repo = SupabaseOpportunityRepository(db_handler=db_handler)
    opportunity = Opportunity(
        id="o-save",
        owner_user_id="u-1",
        account_id="a-1",
        name="Deal Save",
        stage=OpportunityStage.OFFER_SENT,
        status=OpportunityStatus.OPEN,
    )

    repo.save(opportunity)

    params = db_handler.execute_update.call_args.args[1]
    assert params[3] == "OFFER_SENT"
    assert params[4] == "OPEN"
