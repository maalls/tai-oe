"""Tests for OpportunityService.get_opportunity."""

from domain.opportunity import Opportunity
from service.opportunity.opportunity_service import OpportunityService


class _OpportunityRepo:
    def __init__(self, opportunity: Opportunity):
        self.opportunity = opportunity
        self.requested_id = None

    def get_by_id(self, opportunity_id: str) -> Opportunity:
        self.requested_id = opportunity_id
        return self.opportunity

    def save(self, opportunity: Opportunity) -> None:
        self.opportunity = opportunity

    def get_open_by_user(self, user_id: str, limit: int = 100):
        return [self.opportunity]


def test_get_opportunity_returns_repo_entity():
    expected = Opportunity(id="o-1", owner_user_id="u-1", account_id="a-1", name="Deal A")
    repo = _OpportunityRepo(expected)
    service = OpportunityService(repo)

    result = service.get_opportunity("o-1")

    assert result is expected
    assert repo.requested_id == "o-1"