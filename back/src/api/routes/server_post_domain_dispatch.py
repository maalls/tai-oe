"""Domain POST route dispatch for legacy API server."""

import re


def dispatch_post_domain_routes(handler, parsed) -> bool:
    """Dispatch domain POST routes and return True when handled."""
    parsed_path = parsed.path
    entity_update_match = re.match(r"^/api/entity/([^/]+)/([^/]+)$", parsed_path)
    if entity_update_match:
        handler._handle_entity_update_post(entity_update_match)
        return True

    if parsed_path.startswith('/api/emails/classify/'):
        handler._handle_emails_classify_post(parsed_path)
        return True

    if parsed_path == '/api/rfq/generate':
        handler._handle_rfq_generate_post()
        return True

    if parsed_path == '/api/opportunities/create-from-email':
        handler._handle_opportunities_create_from_email_post()
        return True

    if parsed_path == '/api/opportunities/create-manual':
        handler._handle_opportunities_create_manual_post()
        return True

    if parsed_path == '/api/opportunities/create-from-rfp':
        handler._handle_opportunities_create_from_rfp_post()
        return True

    if parsed_path == '/api/email/extract-contact':
        handler._handle_email_extract_contact_post()
        return True

    if parsed_path.startswith('/api/email/auth/'):
        handler._handle_email_auth_status_post(parsed_path)
        return True

    if parsed_path.startswith('/api/email/') and parsed_path.endswith('/resync'):
        handler._handle_email_resync_post(parsed_path)
        return True

    if parsed_path == '/api/email/senders/high-risk':
        handler._handle_email_senders_high_risk_post()
        return True

    if parsed_path == '/api/email/senders/verified':
        handler._handle_email_senders_verified_post()
        return True

    if parsed_path == '/api/imap/config':
        handler._handle_imap_config_post()
        return True

    if parsed_path == '/api/imap/test':
        handler._handle_imap_test_post()
        return True

    if parsed_path == '/api/document/extract-rfp':
        handler._handle_document_extract_rfp_post()
        return True

    if parsed_path == '/api/document/update-content':
        handler._handle_document_update_content_post()
        return True

    return False
