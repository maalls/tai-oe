"""Tests for opportunity-related enums."""

from domain.enums import OpportunityStage, OpportunityStatus


def test_opportunity_stage_values_exist():
    assert OpportunityStage.NEW_LEAD.value == "NEW_LEAD"
    assert OpportunityStage.CLOSED_WON.value == "CLOSED_WON"


def test_opportunity_status_values_exist():
    assert OpportunityStatus.OPEN.value == "OPEN"
    assert OpportunityStatus.WON.value == "WON"
    assert OpportunityStatus.LOST.value == "LOST"
