"""Tests for SupabaseOpportunityRepository."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from domain.enums import OpportunityStage, OpportunityStatus
from domain.opportunity import Opportunity
from infrastructure.exceptions import NotFoundError
from infrastructure.supabase.opportunity_supabase import SupabaseOpportunityRepository


def _mock_supabase_with_data(data):
    supabase = MagicMock()
    query = supabase.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.limit.return_value = query
    query.execute.return_value = MagicMock(data=data)
    return supabase


def test_opportunity_get_by_id_maps_domain():
    supabase = _mock_supabase_with_data([
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
    repo = SupabaseOpportunityRepository(supabase)

    opp = repo.get_by_id("o-1")

    assert opp.id == "o-1"
    assert opp.stage == OpportunityStage.NEGOTIATION
    assert opp.status == OpportunityStatus.OPEN
    assert opp.expected_close_date == date(2026, 6, 1)
    assert opp.created_at == datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)


def test_opportunity_get_by_id_not_found():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseOpportunityRepository(supabase)

    with pytest.raises(NotFoundError):
        repo.get_by_id("missing")


def test_opportunity_save_updates_payload():
    supabase = _mock_supabase_with_data([])
    repo = SupabaseOpportunityRepository(supabase)
    opportunity = Opportunity(
        id="o-save",
        owner_user_id="u-1",
        account_id="a-1",
        name="Deal Save",
        stage=OpportunityStage.OFFER_SENT,
        status=OpportunityStatus.OPEN,
    )

    repo.save(opportunity)

    payload = supabase.table.return_value.update.call_args.args[0]
    assert payload["stage"] == "OFFER_SENT"
    assert payload["status"] == "OPEN"
