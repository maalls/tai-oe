"""Domain POST route dispatch for legacy API server."""

import re

from src.api.document.handler import (
    handle_document_extract_rfp_post,
    handle_document_update_content_post,
)
from src.api.email.routes import dispatch_email_routes
from src.api.entity.handler import handle_entity_update_post
from src.api.opportunity.handler import (
    handle_opportunities_create_from_email_post,
    handle_opportunities_create_from_rfp_post,
    handle_opportunities_create_manual_post,
)
from src.api.rfq.handler import handle_rfq_generate_post


def dispatch_post_domain_routes(handler, parsed) -> bool:
    """Dispatch domain POST routes and return True when handled."""
    parsed_path = parsed.path

    if dispatch_email_routes(handler, "POST", parsed, {}, handler.request_handlers):
        return True

    entity_update_match = re.match(r"^/api/entity/([^/]+)/([^/]+)$", parsed_path)
    if entity_update_match:
        handle_entity_update_post(handler, entity_update_match)
        return True

    if parsed_path == '/api/rfq/generate':
        handle_rfq_generate_post(handler)
        return True

    if parsed_path == '/api/opportunities/create-from-email':
        handle_opportunities_create_from_email_post(handler)
        return True

    if parsed_path == '/api/opportunities/create-manual':
        handle_opportunities_create_manual_post(handler)
        return True

    if parsed_path == '/api/opportunities/create-from-rfp':
        handle_opportunities_create_from_rfp_post(handler)
        return True


    if parsed_path == '/api/document/extract-rfp':
        handle_document_extract_rfp_post(handler)
        return True

    if parsed_path == '/api/document/update-content':
        handle_document_update_content_post(handler)
        return True

    return False
