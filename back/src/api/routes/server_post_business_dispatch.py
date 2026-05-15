"""Business POST route dispatch for legacy API server."""

import re

from src.api.document.handler import (
    handle_chat_attachments_post,
)
from src.api.invoice.routes import dispatch_invoice_routes
from src.api.opportunity.handler import (
    handle_opportunity_rfq_create_from_text_post,
    handle_opportunity_rfq_generate_post,
    handle_send_quote_for_opportunity_post,
)
from src.api.quote.routes import dispatch_quote_routes


def dispatch_post_business_routes(handler, parsed) -> bool:
    """Dispatch opportunity/quote/invoice POST routes and return True when handled."""
    request_handlers = handler.request_handlers

    if dispatch_quote_routes(handler, "POST", parsed, {}, request_handlers):
        return True

    if dispatch_invoice_routes(handler, "POST", parsed, {}, request_handlers):
        return True

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

    return False
