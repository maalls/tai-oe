"""Routing helpers for DDD GET migration endpoints."""

from typing import Any, Dict, Tuple

from src.api.routes.opportunity_routes import get_opportunity_route, advance_opportunity_route
from src.api.routes.vendor_routes import get_vendor_route
from src.api.routes.rfp_routes import get_rfp_route, submit_rfp_route


DDD_GET_ROUTE_MAP = {
    "/api/ddd/opportunity": get_opportunity_route,
    "/api/ddd/opportunity/advance": advance_opportunity_route,
    "/api/ddd/vendor": get_vendor_route,
    "/api/ddd/rfp": get_rfp_route,
    "/api/ddd/rfp/submit": submit_rfp_route,
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
