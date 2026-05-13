"""Application service for RFP operations."""

from src.domain.rfp import Rfp
from src.repository.contracts.rfp_repository import RfpRepositoryContract


class RfpService:
    """Service orchestrating RFP operations via repository contract."""

    def __init__(self, repository: RfpRepositoryContract):
        self.repo = repository

    def get_rfp(self, rfp_id: str) -> Rfp:
        return self.repo.get_by_id(rfp_id)

    def submit_rfp(self, rfp_id: str) -> Rfp:
        rfp = self.repo.get_by_id(rfp_id)
        submitted = rfp.mark_submitted()
        self.repo.save(submitted)
        return submitted
