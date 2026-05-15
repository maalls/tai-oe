"""Domain router for invoice endpoints."""

import re

from src.api.invoice.handler import (
    handle_invoice_pdf_post,
    handle_invoice_send_post,
    handle_quote_invoice_post,
)


def dispatch_invoice_routes(handler, method: str, parsed, _qs, _request_handlers) -> bool:
    """Dispatch invoice routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method != "POST":
        return False

    quote_invoice_match = re.match(r"^/api/quote/([^/]+)/invoice$", path)
    if quote_invoice_match:
        handle_quote_invoice_post(handler, quote_invoice_match)
        return True

    invoice_pdf_match = re.match(r"^/api/invoice/([^/]+)/pdf$", path)
    if invoice_pdf_match:
        handle_invoice_pdf_post(handler, invoice_pdf_match)
        return True

    invoice_send_match = re.match(r"^/api/invoice/([^/]+)/send$", path)
    if invoice_send_match:
        handle_invoice_send_post(handler, invoice_send_match)
        return True

    return False
