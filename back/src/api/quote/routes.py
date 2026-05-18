"""Domain router for quote endpoints."""

import re

from src.api.document.handler import handle_quote_delete


def dispatch_quote_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch quote routes across HTTP methods and return True when handled."""
    del qs, request_handlers
    path = parsed.path

    if method == "DELETE":
        quote_delete_match = re.match(r"^/api/quote/([^/]+)$", path)
        if quote_delete_match:
            handle_quote_delete(handler, quote_delete_match)
            return True

        return False

    return False
