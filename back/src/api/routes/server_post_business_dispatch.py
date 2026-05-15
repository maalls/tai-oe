"""Business POST route dispatch for legacy API server."""

import re

from src.api.document.handler import (
    handle_chat_attachments_post,
)
from src.api.invoice.handler import (
    handle_invoice_pdf_post,
    handle_invoice_send_post,
    handle_quote_invoice_post,
)
from src.api.opportunity.handler import (
    handle_opportunity_rfq_create_from_text_post,
    handle_opportunity_rfq_generate_post,
    handle_send_quote_for_opportunity_post,
)
from src.api.quote.handler import (
    handle_quote_pdf_post,
    handle_quote_update_post,
)


def dispatch_post_business_routes(handler, parsed) -> bool:
    """Dispatch opportunity/quote/invoice POST routes and return True when handled."""
    send_quote_match = re.match(r"^/api/opportunity/([^/]+)/send-quote$", parsed.path)
    if send_quote_match:
        handle_send_quote_for_opportunity_post(handler, send_quote_match)
        return True

    if parsed.path == '/api/chat/attachments':
        handle_chat_attachments_post(handler, parsed)
        return True

    opp_match = re.match(r"^/api/opportunity/([^/]+)/rfq/generate$", parsed.path)
    if opp_match:
        handle_opportunity_rfq_generate_post(handler, opp_match)
        return True

    opp_rfq_create_match = re.match(r"^/api/opportunity/([^/]+)/rfq/create-from-text$", parsed.path)
    if opp_rfq_create_match:
        handle_opportunity_rfq_create_from_text_post(handler, opp_rfq_create_match)
        return True

    quote_pdf_match = re.match(r"^/api/quote/([^/]+)/pdf$", parsed.path)
    if quote_pdf_match:
        handle_quote_pdf_post(handler, quote_pdf_match)
        return True

    quote_invoice_match = re.match(r"^/api/quote/([^/]+)/invoice$", parsed.path)
    if quote_invoice_match:
        handle_quote_invoice_post(handler, quote_invoice_match)
        return True

    invoice_pdf_match = re.match(r"^/api/invoice/([^/]+)/pdf$", parsed.path)
    if invoice_pdf_match:
        handle_invoice_pdf_post(handler, invoice_pdf_match)
        return True

    invoice_send_match = re.match(r"^/api/invoice/([^/]+)/send$", parsed.path)
    if invoice_send_match:
        handle_invoice_send_post(handler, invoice_send_match)
        return True

    quote_update_match = re.match(r"^/api/quote/([^/]+)$", parsed.path)
    if quote_update_match:
        handle_quote_update_post(handler, quote_update_match)
        return True

    return False
