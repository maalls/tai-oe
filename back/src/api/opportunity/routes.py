"""Domain router for opportunity endpoints."""

import re
from typing import Any, Dict, Tuple

from src.api.opportunity.handler import (
    handle_opportunities_create_from_email_post,
    handle_opportunities_create_from_rfp_post,
    handle_opportunities_create_manual_post,
    handle_opportunities_search_get,
    handle_opportunity_delete,
    handle_opportunity_rfq_create_from_text_post,
    handle_opportunity_rfq_generate_post,
    handle_send_quote_for_opportunity_post,
)


def get_opportunity_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle get-opportunity request in a transport-agnostic way."""
    opportunity_id = query.get("opportunity_id")
    if not opportunity_id:
        return {"status": "error", "message": "Missing opportunity_id"}, 400

    result = handlers.handle_get_opportunity(opportunity_id=opportunity_id)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code


def advance_opportunity_route(handlers: Any, query: Dict[str, str]) -> Tuple[Dict[str, Any], int]:
    """Handle advance-opportunity request in a transport-agnostic way."""
    opportunity_id = query.get("opportunity_id")
    stage = query.get("stage")

    if not opportunity_id:
        return {"status": "error", "message": "Missing opportunity_id"}, 400
    if not stage:
        return {"status": "error", "message": "Missing stage"}, 400

    result = handlers.handle_advance_opportunity(opportunity_id=opportunity_id, stage=stage)
    status_code = 200 if result.get("status") == "ok" else 400
    return result, status_code


def dispatch_opportunity_routes(handler, method: str, parsed, qs, request_handlers) -> bool:
    """Dispatch opportunity routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path == '/api/opportunities/search':
            handle_opportunities_search_get(handler, qs, request_handlers)
            return True
        return False

    if method == "POST":
        if path == '/api/opportunities/create-from-email':
            handle_opportunities_create_from_email_post(handler)
            return True

        if path == '/api/opportunities/create-manual':
            handle_opportunities_create_manual_post(handler)
            return True

        if path == '/api/opportunities/create-from-rfp':
            handle_opportunities_create_from_rfp_post(handler)
            return True

        send_quote_match = re.match(r"^/api/opportunity/([^/]+)/send-quote$", path)
        if send_quote_match:
            handle_send_quote_for_opportunity_post(handler, send_quote_match)
            return True

        opp_match = re.match(r"^/api/opportunity/([^/]+)/rfq/generate$", path)
        if opp_match:
            handle_opportunity_rfq_generate_post(handler, opp_match)
            return True

        opp_rfq_create_match = re.match(r"^/api/opportunity/([^/]+)/rfq/create-from-text$", path)
        if opp_rfq_create_match:
            handle_opportunity_rfq_create_from_text_post(handler, opp_rfq_create_match)
            return True

        return False

    if method == "DELETE":
        opportunity_delete_match = re.match(r"^/api/opportunities/([^/]+)$", path)
        if opportunity_delete_match:
            handle_opportunity_delete(handler, opportunity_delete_match)
            return True
        return False

    return False
