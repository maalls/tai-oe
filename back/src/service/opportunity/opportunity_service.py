"""Application service for opportunity operations."""

from src.domain.enums import OpportunityStage
from src.domain.opportunity import Opportunity
from src.repository.contracts.opportunity_repository import OpportunityRepositoryContract


class OpportunityService:
    """Service orchestrating opportunity use-cases."""

    def __init__(self, repository: OpportunityRepositoryContract):
        self.repo = repository

    def get_opportunity(self, opportunity_id: str) -> Opportunity:
        return self.repo.get_by_id(opportunity_id)

    def advance_opportunity(self, opportunity_id: str, stage: OpportunityStage) -> Opportunity:
        opportunity = self.repo.get_by_id(opportunity_id)
        updated = opportunity.advance_stage(stage)
        self.repo.save(updated)
        return updated
