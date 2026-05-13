"""
Fake (in-memory) implementations of repositories for testing
"""
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from domain.email import Email, EmailStatus
from repository.contracts.email_repository import EmailRepositoryContract


class FakeEmailRepository(EmailRepositoryContract):
    """In-memory Email repository for unit tests"""

    def __init__(self):
        self.emails: Dict[str, Email] = {}

    def get_by_id(self, email_id: str) -> Email:
        """Retrieve email by ID from in-memory storage"""
        if email_id not in self.emails:
            raise ValueError(f"Email {email_id} not found")
        return self.emails[email_id]

    def get_all_unclassified(self, limit: int = 100, user_id: str | None = None) -> List[Email]:
        """Retrieve all unclassified emails (UNREAD status)"""
        unclassified = [
            e for e in self.emails.values()
            if e.status == EmailStatus.UNREAD
        ]
        return unclassified[:limit]

    def save(self, email: Email) -> None:
        """Save email to in-memory storage"""
        self.emails[email.id] = email

    def save_many(self, emails: List[Email]) -> None:
        """Save multiple emails to in-memory storage"""
        for email in emails:
            self.save(email)

    def get_all(self) -> List[Email]:
        """Get all emails (useful for testing)"""
        return list(self.emails.values())

    def clear(self) -> None:
        """Clear all emails (useful for test cleanup)"""
        self.emails.clear()
