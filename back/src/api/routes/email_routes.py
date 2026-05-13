"""Email API route adapters for incremental migration.

These helpers are framework-agnostic and can be reused by the current
custom HTTP server or a future FastAPI router.
"""

from typing import Any, Dict, Tuple


def classify_unclassified_route(
    handlers: Any,
    query: Dict[str, str],
    auth_user_id: str | None = None,
) -> Tuple[Dict[str, Any], int]:
    """Handle classify-unclassified request in a transport-agnostic way."""
    user_id = query.get("user_id") or auth_user_id
    if not user_id:
        return {"status": "error", "message": "Missing user_id"}, 400

    try:
        limit = int(query.get("limit", "200"))
    except Exception:
        limit = 200

    result = handlers.handle_classify_unclassified(
        user_id=user_id,
        limit=limit,
    )
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code
