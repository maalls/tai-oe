"""Tests for OpportunityService.advance_opportunity."""

from domain.enums import OpportunityStage
from domain.opportunity import Opportunity
from service.opportunity.opportunity_service import OpportunityService


class _OpportunityRepo:
    def __init__(self, opportunity: Opportunity):
        self.opportunity = opportunity

    def get_by_id(self, opportunity_id: str) -> Opportunity:
        return self.opportunity

    def save(self, opportunity: Opportunity) -> None:
        self.opportunity = opportunity

    def get_open_by_user(self, user_id: str, limit: int = 100):
        return [self.opportunity]


def test_advance_opportunity_persists_new_stage():
    repo = _OpportunityRepo(
        Opportunity(id="o-1", owner_user_id="u-1", account_id="a-1", name="Deal A")
    )
    service = OpportunityService(repo)

    updated = service.advance_opportunity("o-1", OpportunityStage.NEGOTIATION)

    assert updated.stage == OpportunityStage.NEGOTIATION
    assert repo.opportunity.stage == OpportunityStage.NEGOTIATION
