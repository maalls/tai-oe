"""RFP API route adapters for incremental migration."""

from typing import Any, Dict, Tuple


def get_rfp_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle get-rfp request in a transport-agnostic way."""
    rfp_id = query.get("rfp_id")
    if not rfp_id:
        return {"status": "error", "message": "Missing rfp_id"}, 400

    result = handlers.handle_get_rfp(rfp_id=rfp_id)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code


def submit_rfp_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle submit-rfp request in a transport-agnostic way."""
    rfp_id = query.get("rfp_id")
    if not rfp_id:
        return {"status": "error", "message": "Missing rfp_id"}, 400

    result = handlers.handle_submit_rfp(rfp_id=rfp_id)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code
