"""Routing helpers for DDD GET migration endpoints."""

from typing import Any, Dict, Tuple



DDD_GET_ROUTE_MAP = {
}


def is_ddd_get_route(path: str) -> bool:
    """Return whether path is handled by DDD GET migration routing."""
    return path in DDD_GET_ROUTE_MAP


def handle_ddd_get_route(path: str, query: Dict[str, str], handlers: Any) -> Tuple[bool, Dict[str, Any], int]:
    """Route DDD GET paths to their transport-agnostic adapters."""
    adapter = DDD_GET_ROUTE_MAP.get(path)
    if adapter is None:
        return False, {}, 0

    payload, status = adapter(handlers=handlers, query=query)
    return True, payload, status
