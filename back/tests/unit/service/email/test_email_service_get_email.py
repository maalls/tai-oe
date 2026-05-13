"""Unit tests for EmailService.get_email."""

from service.email.email_service import EmailService
from tests.fixtures.sample_data import sample_email


def test_get_email_returns_expected_entity(fake_email_repo):
    email = sample_email(id="e-get")
    fake_email_repo.save(email)

    service = EmailService(fake_email_repo)

    result = service.get_email("e-get")

    assert result.id == "e-get"
    assert result.sender == "sender@example.com"
