from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactBase(BaseModel):
    account_id: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_title: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    account_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_title: Optional[str] = None


class ContactResponse(ContactBase):
    id: str
    created_at: datetime
    account_name: Optional[str] = None
