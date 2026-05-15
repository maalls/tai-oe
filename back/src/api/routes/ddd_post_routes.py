"""Routing helpers for DDD POST migration endpoints."""

from typing import Any, Dict, Tuple

from src.api.opportunity.routes import advance_opportunity_route
from src.api.rfq.routes import submit_rfp_route


DDD_POST_ROUTE_MAP = {
    "/api/ddd/opportunity/advance": advance_opportunity_route,
    "/api/ddd/rfp/submit": submit_rfp_route,
}


def is_ddd_post_route(path: str) -> bool:
    """Return whether path is handled by DDD POST migration routing."""
    return path in DDD_POST_ROUTE_MAP


def handle_ddd_post_route(path: str, payload: Dict[str, str], handlers: Any) -> Tuple[bool, Dict[str, Any], int]:
    """Route DDD POST paths to their transport-agnostic adapters."""
    adapter = DDD_POST_ROUTE_MAP.get(path)
    if adapter is None:
        return False, {}, 0

    result_payload, status = adapter(handlers=handlers, query=payload)
    return True, result_payload, status
