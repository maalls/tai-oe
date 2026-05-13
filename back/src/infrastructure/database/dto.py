"""Pydantic DTOs used for SQL row to domain mapping."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmailDTO(BaseModel):
    """SQL shape for email table rows used by the new repository."""

    model_config = ConfigDict(extra="ignore")

    id: str
    subject: Optional[str] = None
    from_email: str
    body_full: Optional[str] = None
    is_classified: bool = False
    category: Optional[str] = None
    classified_at: Optional[datetime] = None


class OpportunityDTO(BaseModel):
    """SQL shape for opportunity table rows used by repositories."""

    model_config = ConfigDict(extra="ignore")

    id: str
    owner_user_id: Optional[str] = None
    account_id: str
    name: str
    stage: str
    status: str
    amount_estimated: Optional[float] = None
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None
    source: Optional[str] = None
    source_reference_id: Optional[str] = None
    created_at: Optional[datetime] = None


class RfpDTO(BaseModel):
    """SQL shape for RFP documents from the document table."""

    model_config = ConfigDict(extra="ignore")

    id: str
    type: str
    title: str
    status: str
    created_at: Optional[datetime] = None
