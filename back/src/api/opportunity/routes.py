"""Domain router for opportunity endpoints."""

import re

from src.api.opportunity.handler import handle_opportunity_delete


def dispatch_opportunity_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch remaining legacy opportunity DELETE route and return True when handled."""
    _ = qs
    _ = request_handlers
    path = parsed.path

    if method == "DELETE":
        opportunity_delete_match = re.match(r"^/api/opportunities/([^/]+)$", path)
        if opportunity_delete_match:
            handle_opportunity_delete(handler, opportunity_delete_match)
            return True
        return False

    return False
