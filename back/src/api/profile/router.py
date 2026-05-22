from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_auth_service, get_database_repository
from src.repository.repository import DatabaseRepository
from .schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter()

@router.get("/api/profile", response_model=ProfileResponse)
def get_profile(
    user_id: str = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    profile = db.fetch_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(**profile)

@router.put("/api/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    user_id: str = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    updated = db.update_profile(user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(**updated)
