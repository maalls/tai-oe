"""Reusable route access dependency helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse

from src.api.authz.access_policy import can_access_route
from src.api.dependencies import get_auth_service, get_database_repository
from src.repository.repository import DatabaseRepository
from src.service.auth.auth_service import AuthService


DEFAULT_UNAUTHORIZED_BODY = {"error": "Unauthorized"}
DEFAULT_FORBIDDEN_BODY = {"error": "Forbidden"}


@dataclass(frozen=True)
class AccessContext:
    user_id: str
    role: str | None

    def get_user_id(self) -> str:
        return self.user_id


class RouteAccessError(Exception):
    def __init__(self, status_code: int, body: dict[str, Any]):
        super().__init__(str(body))
        self.status_code = status_code
        self.body = dict(body)


def _authorize_request(
    route_path: str,
    authorization: str | None,
    auth_service: AuthService,
    db: DatabaseRepository,
    unauthorized_body: dict[str, Any],
    forbidden_body: dict[str, Any],
    unauthorized_status_code: int,
    forbidden_status_code: int,
) -> str | JSONResponse:
    is_valid, user_data = auth_service.verify_token(authorization or "")
    requester_id = user_data.get("id") if is_valid and user_data else None
    if not requester_id:
        return JSONResponse(dict(unauthorized_body), status_code=unauthorized_status_code)

    profile = db.fetch_profile(requester_id) or {}
    role = profile.get("role")
    if not can_access_route(role, route_path):
        return JSONResponse(dict(forbidden_body), status_code=forbidden_status_code)

    return requester_id


def _authorize_request_or_raise(
    route_path: str,
    authorization: str | None,
    auth_service: AuthService,
    db: DatabaseRepository,
    unauthorized_body: dict[str, Any],
    forbidden_body: dict[str, Any],
    unauthorized_status_code: int,
    forbidden_status_code: int,
) -> AccessContext:
    is_valid, user_data = auth_service.verify_token(authorization or "")
    requester_id = user_data.get("id") if is_valid and user_data else None
    if not requester_id:
        raise RouteAccessError(status_code=unauthorized_status_code, body=unauthorized_body)

    profile = db.fetch_profile(requester_id) or {}
    role = profile.get("role")
    if not can_access_route(role, route_path):
        raise RouteAccessError(status_code=forbidden_status_code, body=forbidden_body)

    return AccessContext(user_id=requester_id, role=role)


def build_route_access_dependency(
    route_path: str,
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
        return _authorize_request(
            route_path=route_path,
            authorization=authorization,
            auth_service=auth_service,
            db=db,
            unauthorized_body=unauthorized_body,
            forbidden_body=forbidden_body,
            unauthorized_status_code=unauthorized_status_code,
            forbidden_status_code=forbidden_status_code,
        )

    return _dependency


def build_current_route_access_dependency(
    unauthorized_body: dict[str, Any],
    forbidden_body: dict[str, Any],
    unauthorized_status_code: int = 401,
    forbidden_status_code: int = 403,
) -> Callable[..., str | JSONResponse]:
    """Build a dependency that authorizes against the current FastAPI route path."""

    def _dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        auth_service: AuthService = Depends(get_auth_service),
        db: DatabaseRepository = Depends(get_database_repository),
    ) -> str | JSONResponse:
        route = request.scope.get("route")
        route_path = getattr(route, "path", None)
        if not route_path:
            return JSONResponse(dict(forbidden_body), status_code=forbidden_status_code)

        return _authorize_request(
            route_path=route_path,
            authorization=authorization,
            auth_service=auth_service,
            db=db,
            unauthorized_body=unauthorized_body,
            forbidden_body=forbidden_body,
            unauthorized_status_code=unauthorized_status_code,
            forbidden_status_code=forbidden_status_code,
        )

    return _dependency


def build_default_route_access_dependency() -> Callable[..., str | JSONResponse]:
    """Build a dependency using the default Unauthorized/Forbidden error payloads."""

    return build_current_route_access_dependency(
        unauthorized_body=DEFAULT_UNAUTHORIZED_BODY,
        forbidden_body=DEFAULT_FORBIDDEN_BODY,
    )


def build_access_context_dependency(
    unauthorized_body: dict[str, Any],
    forbidden_body: dict[str, Any],
    unauthorized_status_code: int = 401,
    forbidden_status_code: int = 403,
) -> Callable[..., AccessContext]:
    """Build a dependency returning an AccessContext or raising RouteAccessError."""

    def _dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        auth_service: AuthService = Depends(get_auth_service),
        db: DatabaseRepository = Depends(get_database_repository),
    ) -> AccessContext:
        route = request.scope.get("route")
        route_path = getattr(route, "path", None)
        if not route_path:
            raise RouteAccessError(status_code=forbidden_status_code, body=forbidden_body)

        return _authorize_request_or_raise(
            route_path=route_path,
            authorization=authorization,
            auth_service=auth_service,
            db=db,
            unauthorized_body=unauthorized_body,
            forbidden_body=forbidden_body,
            unauthorized_status_code=unauthorized_status_code,
            forbidden_status_code=forbidden_status_code,
        )

    return _dependency


def build_default_access_context_dependency() -> Callable[..., AccessContext]:
    """Build an AccessContext dependency using default Unauthorized/Forbidden payloads."""

    return build_access_context_dependency(
        unauthorized_body=DEFAULT_UNAUTHORIZED_BODY,
        forbidden_body=DEFAULT_FORBIDDEN_BODY,
    )
