"""
Tests for Email domain entity
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
from domain.email import Email
from domain.enums import EmailStatus
from tests.fixtures.sample_data import sample_email, sample_email_unclassified, sample_email_classified


class TestEmailEntity:
    """Test Email domain entity"""

    def test_email_creation(self):
        """Test creating an Email instance"""
        email = sample_email()
        assert email.id == "test-1"
        assert email.status == EmailStatus.UNREAD
        assert email.classification is None

    def test_email_immutability(self):
        """Test that Email is immutable (frozen dataclass)"""
        email = sample_email()
        with pytest.raises(Exception):  # FrozenInstanceError
            email.status = EmailStatus.CLASSIFIED

    def test_email_mark_classified_success(self):
        """Test marking email as classified"""
        email = sample_email_unclassified()
        classified = email.mark_classified("quote")

        # New instance should have new status
        assert classified.status == EmailStatus.CLASSIFIED
        assert classified.classification == "quote"
        assert classified.classified_at is not None

        # Original should be unchanged (immutable)
        assert email.status == EmailStatus.UNREAD
        assert email.classification is None

    def test_email_mark_classified_already_classified(self):
        """Test that classified email cannot be classified again"""
        email = sample_email_classified(category="quote")

        with pytest.raises(ValueError) as exc_info:
            email.mark_classified("invoice")

        assert "already classified" in str(exc_info.value).lower()

    def test_email_mark_classified_twice_fails(self):
        """Test workflow: mark classified, try again, should fail"""
        email = sample_email_unclassified()
        classified = email.mark_classified("quote")

        # Try to classify the already-classified version
        with pytest.raises(ValueError):
            classified.mark_classified("invoice")

    def test_email_archive(self):
        """Test archiving an email"""
        email = sample_email_unclassified()
        archived = email.archive()

        assert archived.status == EmailStatus.ARCHIVED
        assert email.status == EmailStatus.UNREAD  # Original unchanged

    def test_email_with_all_fields(self):
        """Test creating email with all fields"""
        email = Email(
            id="full-test",
            subject="Full test subject",
            body="Full test body",
            sender="full@example.com",
            status=EmailStatus.CLASSIFIED,
            classification="invoice",
        )

        assert email.subject == "Full test subject"
        assert email.sender == "full@example.com"
        assert email.classification == "invoice"
