"""Tests for Opportunity domain entity."""

from datetime import date, datetime, timezone

import pytest

from domain.enums import OpportunityStage, OpportunityStatus
from domain.opportunity import Opportunity


def test_advance_stage_returns_new_entity():
    created_at = datetime(2026, 5, 13, 10, 20, 30, tzinfo=timezone.utc)
    opp = Opportunity(
        id="o-1",
        owner_user_id="u-1",
        account_id="a-1",
        name="Deal",
        created_at=created_at,
        expected_close_date=date(2026, 6, 1),
    )

    updated = opp.advance_stage(OpportunityStage.NEGOTIATION)

    assert updated.stage == OpportunityStage.NEGOTIATION
    assert opp.stage == OpportunityStage.NEW_LEAD
    assert updated.created_at == created_at
    assert updated.expected_close_date == date(2026, 6, 1)
    assert opp.created_at == created_at


def test_mark_won_sets_stage_and_status():
    opp = Opportunity(
        id="o-2",
        owner_user_id="u-1",
        account_id="a-1",
        name="Deal",
        amount_estimated=12500.0,
        probability=42,
    )

    won = opp.mark_won()

    assert won.stage == OpportunityStage.CLOSED_WON
    assert won.status == OpportunityStatus.WON
    assert won.amount_estimated == 12500.0
    assert won.probability == 42
    assert opp.stage == OpportunityStage.NEW_LEAD
    assert opp.status == OpportunityStatus.OPEN


def test_mark_lost_sets_stage_and_status():
    opp = Opportunity(
        id="o-3",
        owner_user_id="u-1",
        account_id="a-1",
        name="Deal",
        source="manual",
        source_reference_id="ref-1",
    )

    lost = opp.mark_lost()

    assert lost.stage == OpportunityStage.CLOSED_LOST
    assert lost.status == OpportunityStatus.LOST
    assert lost.source == "manual"
    assert lost.source_reference_id == "ref-1"
    assert opp.stage == OpportunityStage.NEW_LEAD
    assert opp.status == OpportunityStatus.OPEN


def test_opportunity_defaults_and_immutability():
    opp = Opportunity(id="o-4", owner_user_id=None, account_id="a-1", name="Deal")

    assert opp.stage == OpportunityStage.NEW_LEAD
    assert opp.status == OpportunityStatus.OPEN
    assert opp.amount_estimated == 0.0
    assert opp.probability == 10
    assert opp.expected_close_date is None
    assert opp.created_at is None

    with pytest.raises(Exception):
        opp.name = "Changed"
