"""Central role-to-route access policy for API authorization."""

from __future__ import annotations

from typing import Final

_ACCESS_POLICY: Final[dict[str, set[str]]] = {
    "admin.users.list": {"admin"},
    "admin.users.update_role": {"admin"},
    "csv.access": {"admin"},
    "csv.query": {"admin"},
    "utils.email_fetch_loop.status": {"admin"},
    "utils.prompt.read": {"admin"},
    "utils.unsafe": {"admin"},
}


def allowed_roles_for_route(route_key: str) -> set[str]:
    """Return allowed roles for a route key; empty set means deny by default."""
    return set(_ACCESS_POLICY.get(route_key, set()))


def can_access_route(role: str | None, route_key: str) -> bool:
    """Return True when role is allowed for the given route key."""
    if not role:
        return False

    return role in allowed_roles_for_route(route_key)
