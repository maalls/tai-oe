"""Domain router for RFQ/RFP endpoints."""

from src.api.rfq.handler import handle_rfq_generate_post, handle_rfp_post


def dispatch_rfq_routes(handler, method: str, parsed, _qs, _request_handlers) -> bool:
    """Dispatch RFQ/RFP routes across HTTP methods and return True when handled."""
    if method != "POST":
        return False

    path = parsed.path

    if path == '/api/rfq/generate':
        handle_rfq_generate_post(handler)
        return True

    if path == '/api/rfp':
        handle_rfp_post(handler)
        return True

    return False
