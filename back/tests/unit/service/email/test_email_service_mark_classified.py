"""Unit tests for EmailService.mark_classified."""

from domain.enums import EmailStatus
from service.email.email_service import EmailService
from tests.fixtures.sample_data import sample_email


def test_mark_classified_updates_and_persists(fake_email_repo):
    email = sample_email(id="e-mark", status=EmailStatus.UNREAD)
    fake_email_repo.save(email)

    service = EmailService(fake_email_repo)

    result = service.mark_classified("e-mark", "rfp")

    assert result.status == EmailStatus.CLASSIFIED
    assert result.classification == "rfp"
    persisted = fake_email_repo.get_by_id("e-mark")
    assert persisted.status == EmailStatus.CLASSIFIED
    assert persisted.classification == "rfp"
