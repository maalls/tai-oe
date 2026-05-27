"""Admin API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from src.api.dependencies import get_auth_service, get_database_repository
from src.repository.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService

router = APIRouter(tags=["admin"])

_ALLOWED_ROLES = {"admin", "user"}


def _resolve_requester_id(
    authorization: str | None,
    auth_service: AuthService,
) -> str | None:
    is_valid, user_data = auth_service.verify_token(authorization or "")
    if not is_valid or not user_data:
        return None
    return user_data.get("id")


def _assert_admin_user(
    requester_id: str,
    db: DatabaseRepository,
) -> bool:
    profile = db.fetch_profile(requester_id) or {}
    return profile.get("role") == "admin"


@router.get("/api/admin/users")
def admin_list_users(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    requester_id = _resolve_requester_id(authorization, auth_service)
    if not requester_id:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)

    if not _assert_admin_user(requester_id, db):
        return JSONResponse({"status": "error", "message": "Forbidden"}, status_code=403)

    users = db.list_users(limit=100, offset=0)
    return JSONResponse({"status": "ok", "users": users}, status_code=200)


@router.patch("/api/admin/users/{target_user_id}/role")
def admin_update_user_role(
    target_user_id: str,
    payload: dict[str, Any],
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    requester_id = _resolve_requester_id(authorization, auth_service)
    if not requester_id:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)

    if not _assert_admin_user(requester_id, db):
        return JSONResponse({"status": "error", "message": "Forbidden"}, status_code=403)

    role = payload.get("role") if isinstance(payload, dict) else None
    if role not in _ALLOWED_ROLES:
        return JSONResponse(
            {"status": "error", "message": "Invalid role. Allowed values: admin, user"},
            status_code=400,
        )

    if requester_id == target_user_id and role != "admin":
        return JSONResponse(
            {"status": "error", "message": "Self-demotion is not allowed"},
            status_code=400,
        )

    updated = db.set_user_role(target_user_id, role)
    if not updated:
        return JSONResponse({"status": "error", "message": "User not found"}, status_code=404)

    return JSONResponse({"status": "ok", "user": updated}, status_code=200)
