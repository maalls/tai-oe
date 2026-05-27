"""Central role-to-route access policy for API authorization."""

from __future__ import annotations

from typing import Final

_ACCESS_POLICY: Final[dict[str, set[str]]] = {
    "/api/admin/users": {"admin"},
    "/api/admin/users/{target_user_id}/role": {"admin"},
    "/api/csv/sources": {"admin"},
    "/api/csv/files": {"admin"},
    "/api/csv/preview": {"admin"},
    "/api/csv/source": {"admin"},
    "/api/csv/raw": {"admin"},
    "/api/csv/download": {"admin"},
    "/api/csv/query": {"admin"},
    "/api/email-fetch-loop/status": {"admin"},
    "/api/fetch": {"admin"},
    "/api/curl": {"admin"},
    "/api/fs/create": {"admin"},
    "/api/fs/read": {"admin"},
    "/api/prompt/{relative_path:path}": {"admin"},
    "/api/storage/{raw_filename:path}": {"admin", "user"},
}


def allowed_roles_for_route(route_path: str) -> set[str]:
    """Return allowed roles for a route path; empty set means deny by default."""
    return set(_ACCESS_POLICY.get(route_path, set()))


def can_access_route(role: str | None, route_path: str) -> bool:
    """Return True when role is allowed for the given route path."""
    if not role:
        return False

    return role in allowed_roles_for_route(route_path)
