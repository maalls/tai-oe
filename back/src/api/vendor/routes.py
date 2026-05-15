"""Vendor API route adapters for incremental migration."""

from typing import Any, Dict, Tuple


def get_vendor_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle get-vendor request in a transport-agnostic way."""
    vendor_id = query.get("vendor_id")
    if not vendor_id:
        return {"status": "error", "message": "Missing vendor_id"}, 400

    result = handlers.handle_get_vendor(vendor_id=vendor_id)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code
