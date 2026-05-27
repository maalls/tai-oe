"""Admin API routes."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.authz.route_access import build_route_access_dependency
from src.api.dependencies import get_database_repository
from src.repository.repository import DatabaseRepository

router = APIRouter(tags=["admin"])

_ALLOWED_ROLES = {"admin", "user"}

_admin_users_list_access = build_route_access_dependency(
    route_path="/api/admin/users",
    unauthorized_body={"status": "error", "message": "Unauthorized"},
    forbidden_body={"status": "error", "message": "Forbidden"},
)

_admin_users_update_role_access = build_route_access_dependency(
    route_path="/api/admin/users/{target_user_id}/role",
    unauthorized_body={"status": "error", "message": "Unauthorized"},
    forbidden_body={"status": "error", "message": "Forbidden"},
)


@router.get("/api/admin/users")
def admin_list_users(
    requester_id: str | JSONResponse = Depends(_admin_users_list_access),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

    users = db.list_users(limit=100, offset=0)
    return JSONResponse(jsonable_encoder({"status": "ok", "users": users}), status_code=200)


@router.patch("/api/admin/users/{target_user_id}/role")
def admin_update_user_role(
    target_user_id: str,
    payload: dict[str, Any],
    requester_id: str | JSONResponse = Depends(_admin_users_update_role_access),
    db: DatabaseRepository = Depends(get_database_repository),
):
    if isinstance(requester_id, JSONResponse):
        return requester_id

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

    return JSONResponse(jsonable_encoder({"status": "ok", "user": updated}), status_code=200)
