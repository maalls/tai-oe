"""RFP domain entity."""

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from src.domain.enums import DocumentStatus


@dataclass(frozen=True)
class Rfp:
    """Immutable RFP entity."""

    id: str
    title: str
    requester_email: Optional[str]
    content: Optional[str]
    status: DocumentStatus = DocumentStatus.DRAFT
    created_at: Optional[datetime] = None

    def mark_submitted(self) -> "Rfp":
        """Move RFP to submitted status."""
        if self.status == DocumentStatus.SUBMITTED:
            raise ValueError("RFP already submitted")
        return replace(self, status=DocumentStatus.SUBMITTED)
