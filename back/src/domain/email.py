"""
Email Domain Entity - Pure business logic, no framework dependencies
"""
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional
from src.domain.enums import EmailStatus


@dataclass(frozen=True)
class Email:
    """Immutable Email entity"""
    id: str
    subject: Optional[str]
    body: Optional[str]
    sender: str
    status: EmailStatus
    classification: Optional[str] = None
    classified_at: Optional[datetime] = None

    def mark_classified(self, category: str) -> "Email":
        """
        Mark email as classified. Returns new Email instance (immutable).
        
        Args:
            category: Classification category (e.g., 'quote', 'invoice')
            
        Returns:
            New Email instance with CLASSIFIED status
            
        Raises:
            ValueError: If already classified
        """
        if self.status == EmailStatus.CLASSIFIED:
            raise ValueError(f"Email {self.id} already classified as '{self.classification}'")
        
        return replace(
            self,
            status=EmailStatus.CLASSIFIED,
            classification=category,
            classified_at=datetime.now()
        )

    def archive(self) -> "Email":
        """Mark email as archived. Returns new Email instance."""
        return replace(self, status=EmailStatus.ARCHIVED)
