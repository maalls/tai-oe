"""Reusable route access dependency helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends, Header
from fastapi.responses import JSONResponse

from src.api.authz.access_policy import can_access_route
from src.api.dependencies import get_auth_service, get_database_repository
from src.repository.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService


def build_route_access_dependency(
    route_key: str,
    unauthorized_body: dict[str, Any],
    forbidden_body: dict[str, Any],
    unauthorized_status_code: int = 401,
    forbidden_status_code: int = 403,
) -> Callable[..., str | JSONResponse]:
    """Build a dependency that returns requester_id or an error JSONResponse."""

    def _dependency(
        authorization: str | None = Header(default=None),
        auth_service: AuthService = Depends(get_auth_service),
        db: DatabaseRepository = Depends(get_database_repository),
    ) -> str | JSONResponse:
        is_valid, user_data = auth_service.verify_token(authorization or "")
        requester_id = user_data.get("id") if is_valid and user_data else None
        if not requester_id:
            return JSONResponse(dict(unauthorized_body), status_code=unauthorized_status_code)

        profile = db.fetch_profile(requester_id) or {}
        role = profile.get("role")
        if not can_access_route(role, route_key):
            return JSONResponse(dict(forbidden_body), status_code=forbidden_status_code)

        return requester_id

    return _dependency
