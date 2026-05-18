from pydantic import BaseModel, EmailStr
from typing import Optional

class ProfileResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
