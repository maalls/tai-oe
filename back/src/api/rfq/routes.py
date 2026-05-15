"""Domain router for RFQ/RFP endpoints."""

from typing import Any, Dict, Tuple

from src.api.rfq.handler import handle_rfq_generate_post, handle_rfp_post


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


def dispatch_rfq_routes(handler, method: str, parsed, _qs, _request_handlers) -> bool:
    """Dispatch RFQ/RFP routes across HTTP methods and return True when handled."""
    if method != "POST":
        return False

    path = parsed.path

    if path == '/api/rfq/generate':
        handle_rfq_generate_post(handler)
        return True

    if path == '/api/rfp':
        handle_rfp_post(handler)
        return True

    return False
