"""
Sample data factories for testing
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from domain.email import Email
from domain.enums import EmailStatus


def sample_email(
    id: str = "test-1",
    status: EmailStatus = EmailStatus.UNREAD,
    classification: Optional[str] = None,
    classified_at: Optional[datetime] = None
) -> Email:
    """
    Factory function to create sample Email instances for tests.
    
    Args:
        id: Email ID
        status: Email status
        classification: Classification category (if classified)
        classified_at: Classification timestamp
        
    Returns:
        Email instance
    """
    return Email(
        id=id,
        subject="Test email subject",
        body="This is a test email body with some content.",
        sender="sender@example.com",
        status=status,
        classification=classification,
        classified_at=classified_at
    )


def sample_email_unclassified(id: str = "test-unclassified") -> Email:
    """Factory for unclassified email"""
    return sample_email(id=id, status=EmailStatus.UNREAD)


def sample_email_classified(id: str = "test-classified", category: str = "quote") -> Email:
    """Factory for classified email"""
    return sample_email(
        id=id,
        status=EmailStatus.CLASSIFIED,
        classification=category,
        classified_at=datetime.now()
    )
