"""Opportunity API route adapters for incremental migration."""

from typing import Any, Dict, Tuple


def get_opportunity_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle get-opportunity request in a transport-agnostic way."""
    opportunity_id = query.get("opportunity_id")
    if not opportunity_id:
        return {"status": "error", "message": "Missing opportunity_id"}, 400

    result = handlers.handle_get_opportunity(opportunity_id=opportunity_id)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code


def advance_opportunity_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle advance-opportunity request in a transport-agnostic way."""
    opportunity_id = query.get("opportunity_id")
    stage = query.get("stage")

    if not opportunity_id:
        return {"status": "error", "message": "Missing opportunity_id"}, 400
    if not stage:
        return {"status": "error", "message": "Missing stage"}, 400

    result = handlers.handle_advance_opportunity(opportunity_id=opportunity_id, stage=stage)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code
