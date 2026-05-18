"""Domain router for document endpoints."""

import re

from src.api.document.handler import handle_document_delete


def dispatch_document_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch remaining legacy document DELETE route and return True when handled."""
    _ = qs
    _ = request_handlers
    path = parsed.path

    if method == "DELETE":
        document_delete_match = re.match(r"^/api/document/([^/]+)$", path)
        if document_delete_match:
            handle_document_delete(handler, document_delete_match)
            return True

        return False

    return False
