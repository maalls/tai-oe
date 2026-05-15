"""Domain POST route dispatch for legacy API server."""

import re

from src.api.routes.server_post_utility_handlers import (
    handle_document_extract_rfp_post,
    handle_document_update_content_post,
    handle_email_auth_status_post,
    handle_email_extract_contact_post,
    handle_email_resync_post,
    handle_email_senders_high_risk_post,
    handle_email_senders_verified_post,
    handle_emails_classify_post,
    handle_entity_update_post,
    handle_imap_config_post,
    handle_imap_test_post,
    handle_opportunities_create_from_email_post,
    handle_opportunities_create_from_rfp_post,
    handle_opportunities_create_manual_post,
    handle_rfq_generate_post,
)


def dispatch_post_domain_routes(handler, parsed) -> bool:
    """Dispatch domain POST routes and return True when handled."""
    parsed_path = parsed.path
    entity_update_match = re.match(r"^/api/entity/([^/]+)/([^/]+)$", parsed_path)
    if entity_update_match:
        handle_entity_update_post(handler, entity_update_match)
        return True

    if parsed_path.startswith('/api/emails/classify/'):
        handle_emails_classify_post(handler, parsed_path)
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

    if parsed_path == '/api/email/extract-contact':
        handle_email_extract_contact_post(handler)
        return True

    if parsed_path.startswith('/api/email/auth/'):
        handle_email_auth_status_post(handler, parsed_path)
        return True

    if parsed_path.startswith('/api/email/') and parsed_path.endswith('/resync'):
        handle_email_resync_post(handler, parsed_path)
        return True

    if parsed_path == '/api/email/senders/high-risk':
        handle_email_senders_high_risk_post(handler)
        return True

    if parsed_path == '/api/email/senders/verified':
        handle_email_senders_verified_post(handler)
        return True

    if parsed_path == '/api/imap/config':
        handle_imap_config_post(handler)
        return True

    if parsed_path == '/api/imap/test':
        handle_imap_test_post(handler)
        return True

    if parsed_path == '/api/document/extract-rfp':
        handle_document_extract_rfp_post(handler)
        return True

    if parsed_path == '/api/document/update-content':
        handle_document_update_content_post(handler)
        return True

    return False
