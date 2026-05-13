"""Opportunity domain entity."""

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Optional

from src.domain.enums import OpportunityStage, OpportunityStatus


@dataclass(frozen=True)
class Opportunity:
    """Immutable sales opportunity entity."""

    id: str
    owner_user_id: Optional[str]
    account_id: str
    name: str
    stage: OpportunityStage = OpportunityStage.NEW_LEAD
    status: OpportunityStatus = OpportunityStatus.OPEN
    amount_estimated: float = 0.0
    probability: int = 10
    expected_close_date: Optional[date] = None
    source: Optional[str] = None
    source_reference_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def advance_stage(self, stage: OpportunityStage) -> "Opportunity":
        """Advance opportunity stage without mutating the original object."""
        return replace(self, stage=stage)

    def mark_won(self) -> "Opportunity":
        """Transition to won state and closed_won stage."""
        return replace(self, stage=OpportunityStage.CLOSED_WON, status=OpportunityStatus.WON)

    def mark_lost(self) -> "Opportunity":
        """Transition to lost state and closed_lost stage."""
        return replace(self, stage=OpportunityStage.CLOSED_LOST, status=OpportunityStatus.LOST)
