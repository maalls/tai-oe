"""Domain router for quote endpoints."""

import re

from src.api.document.handler import handle_quote_delete
from src.api.quote.handler import (
    handle_quote_pdf_post,
    handle_quote_send_post,
    handle_quote_submit_post,
    handle_quote_update_post,
    handle_quotes_download_get,
    handle_quotes_list_get,
)


def dispatch_quote_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch quote routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path == '/api/quotes/list':
            handle_quotes_list_get(handler, request_handlers)
            return True

        if path.startswith('/api/quotes/download/'):
            handle_quotes_download_get(handler, path, qs, request_handlers)
            return True

        return False

    if method == "POST":
        if path == '/api/quote':
            handle_quote_submit_post(handler)
            return True

        if path == '/api/quote/send':
            handle_quote_send_post(handler)
            return True

        quote_pdf_match = re.match(r"^/api/quote/([^/]+)/pdf$", path)
        if quote_pdf_match:
            handle_quote_pdf_post(handler, quote_pdf_match)
            return True

        quote_update_match = re.match(r"^/api/quote/([^/]+)$", path)
        if quote_update_match:
            handle_quote_update_post(handler, quote_update_match)
            return True

        return False

    if method == "DELETE":
        quote_delete_match = re.match(r"^/api/quote/([^/]+)$", path)
        if quote_delete_match:
            handle_quote_delete(handler, quote_delete_match)
            return True

        return False

    return False
