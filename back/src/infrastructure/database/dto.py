"""Pydantic DTOs used for SQL row to domain mapping."""

from datetime import datetime
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
