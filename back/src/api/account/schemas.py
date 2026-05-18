from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class AccountBase(BaseModel):
    name: str
    vat_number: Optional[str] = None
    siret: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    payment_terms_default: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    vat_number: Optional[str] = None
    siret: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    payment_terms_default: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None

class AccountResponse(AccountBase):
    id: str
    created_at: datetime
    updated_at: datetime
