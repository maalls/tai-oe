"""Admin API routes."""

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.api.authz.route_access import AccessContext, build_default_access_context_dependency
from src.api.dependencies import get_auth_service, get_database_repository
from src.repository.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService

router = APIRouter(tags=["admin"])

_ALLOWED_ROLES = {"admin", "user"}

_admin_access = build_default_access_context_dependency()


def _normalize_email(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.strip()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        return ""
    return normalized


@router.post("/api/admin/users")
def admin_create_user(
    payload: dict[str, Any],
    requester: AccessContext = Depends(_admin_access),
    auth_service: AuthService = Depends(get_auth_service),
    db: DatabaseRepository = Depends(get_database_repository),
):
    _ = requester

    email = _normalize_email(payload.get("email") if isinstance(payload, dict) else None)
    password = payload.get("password") if isinstance(payload, dict) else None
    full_name = payload.get("full_name") if isinstance(payload, dict) else None
    role = payload.get("role") if isinstance(payload, dict) else "user"

    if not email:
        return JSONResponse({"status": "error", "message": "Invalid email"}, status_code=400)
    if not isinstance(password, str) or not password.strip():
        return JSONResponse(
            {"status": "error", "message": "Password is required"},
            status_code=400,
        )
    if role not in _ALLOWED_ROLES:
        return JSONResponse(
            {"status": "error", "message": "Invalid role. Allowed values: admin, user"},
            status_code=400,
        )

    signup_result = auth_service.signup(email=email, password=password)
    signup_status = signup_result.get("status")
    if isinstance(signup_status, int) and signup_status >= 400:
        message = signup_result.get("error") or "Failed to create user"
        return JSONResponse({"status": "error", "message": str(message)}, status_code=signup_status)

    created_user = signup_result.get("user") if isinstance(signup_result.get("user"), dict) else {}
    user_id = created_user.get("id")
    user_email = created_user.get("email", email)
    if not user_id:
        return JSONResponse(
            {"status": "error", "message": "Created user payload is missing id"},
            status_code=500,
        )

    # Force la création du profil si absent
    db.insert_profile(user_id, user_email, full_name.strip() if isinstance(full_name, str) else None, role)

    if role != "user":
        updated_role = db.set_user_role(user_id, role)
        if not updated_role:
            return JSONResponse(
                {"status": "error", "message": "User created but role update failed"},
                status_code=500,
            )

    if isinstance(full_name, str) and full_name.strip():
        db.update_profile(user_id, {"full_name": full_name.strip()})

    user_payload = db.get_user_by_id(user_id)
    if not user_payload:
        user_payload = {
            "id": user_id,
            "email": user_email,
            "full_name": full_name.strip() if isinstance(full_name, str) else None,
            "role": role,
            "created_at": None,
        }

    return JSONResponse(jsonable_encoder({"status": "ok", "user": user_payload}), status_code=201)


@router.get("/api/admin/users")
def admin_list_users(
    requester: AccessContext = Depends(_admin_access),
    db: DatabaseRepository = Depends(get_database_repository),
):
    users = db.list_users(limit=100, offset=0)
    return JSONResponse(jsonable_encoder({"status": "ok", "users": users}), status_code=200)


@router.patch("/api/admin/users/{target_user_id}/role")
def admin_update_user_role(
    target_user_id: str,
    payload: dict[str, Any],
    requester: AccessContext = Depends(_admin_access),
    db: DatabaseRepository = Depends(get_database_repository),
):
    requester_id = requester.get_user_id()

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
