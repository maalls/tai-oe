"""Unit tests for EmailService.get_all_unclassified."""

from domain.enums import EmailStatus
from service.email.email_service import EmailService
from tests.fixtures.sample_data import sample_email


def test_get_all_unclassified_filters_classified(fake_email_repo):
    unread = sample_email(id="e-unread", status=EmailStatus.UNREAD)
    classified = sample_email(id="e-classified", status=EmailStatus.CLASSIFIED, classification="quote")
    fake_email_repo.save(unread)
    fake_email_repo.save(classified)

    service = EmailService(fake_email_repo)

    results = service.get_all_unclassified(limit=10)

    assert len(results) == 1
    assert results[0].id == "e-unread"
