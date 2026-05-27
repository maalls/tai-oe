from pydantic import BaseModel, EmailStr
from typing import Optional

class ProfileResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
