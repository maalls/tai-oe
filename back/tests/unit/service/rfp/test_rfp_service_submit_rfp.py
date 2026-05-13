"""Tests for RfpService.submit_rfp."""

from domain.enums import DocumentStatus
from domain.rfp import Rfp
from service.rfp.rfp_service import RfpService


class _RfpRepo:
    def __init__(self, rfp: Rfp):
        self.rfp = rfp
        self.requested_id = None

    def get_by_id(self, rfp_id: str) -> Rfp:
        self.requested_id = rfp_id
        return self.rfp

    def save(self, rfp: Rfp) -> None:
        self.rfp = rfp


def test_submit_rfp_persists_submitted_status():
    repo = _RfpRepo(
        Rfp(id="r-1", title="Need quote", requester_email="a@b.com", content="...", status=DocumentStatus.DRAFT)
    )
    original = repo.rfp
    service = RfpService(repo)

    result = service.submit_rfp("r-1")

    assert result.status == DocumentStatus.SUBMITTED
    assert original.status == DocumentStatus.DRAFT
    assert repo.rfp.status == DocumentStatus.SUBMITTED
    assert repo.requested_id == "r-1"
