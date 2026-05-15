"""Business POST route dispatch for legacy API server."""

import re


def dispatch_post_business_routes(handler, parsed) -> bool:
    """Dispatch opportunity/quote/invoice POST routes and return True when handled."""
    send_quote_match = re.match(r"^/api/opportunity/([^/]+)/send-quote$", parsed.path)
    if send_quote_match:
        handler._handle_send_quote_for_opportunity_post(send_quote_match)
        return True

    if parsed.path == '/api/chat/attachments':
        handler._handle_chat_attachments_post(parsed)
        return True

    opp_match = re.match(r"^/api/opportunity/([^/]+)/rfq/generate$", parsed.path)
    if opp_match:
        handler._handle_opportunity_rfq_generate_post(opp_match)
        return True

    opp_rfq_create_match = re.match(r"^/api/opportunity/([^/]+)/rfq/create-from-text$", parsed.path)
    if opp_rfq_create_match:
        handler._handle_opportunity_rfq_create_from_text_post(opp_rfq_create_match)
        return True

    quote_pdf_match = re.match(r"^/api/quote/([^/]+)/pdf$", parsed.path)
    if quote_pdf_match:
        handler._handle_quote_pdf_post(quote_pdf_match)
        return True

    quote_invoice_match = re.match(r"^/api/quote/([^/]+)/invoice$", parsed.path)
    if quote_invoice_match:
        handler._handle_quote_invoice_post(quote_invoice_match)
        return True

    invoice_pdf_match = re.match(r"^/api/invoice/([^/]+)/pdf$", parsed.path)
    if invoice_pdf_match:
        handler._handle_invoice_pdf_post(invoice_pdf_match)
        return True

    invoice_send_match = re.match(r"^/api/invoice/([^/]+)/send$", parsed.path)
    if invoice_send_match:
        handler._handle_invoice_send_post(invoice_send_match)
        return True

    quote_update_match = re.match(r"^/api/quote/([^/]+)$", parsed.path)
    if quote_update_match:
        handler._handle_quote_update_post(quote_update_match)
        return True

    return False
