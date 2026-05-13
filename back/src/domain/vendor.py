"""Vendor domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Vendor:
    """Immutable vendor entity."""

    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None
