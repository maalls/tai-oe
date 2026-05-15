"""DELETE route dispatch for legacy API server."""

import re


def dispatch_delete_request(handler, parsed_path: str) -> bool:
    """Dispatch DELETE routes and return True when handled."""
    opportunity_delete_match = re.match(r"^/api/opportunities/([^/]+)$", parsed_path)
    if opportunity_delete_match:
        handler._handle_opportunity_delete(opportunity_delete_match)
        return True

    quote_delete_match = re.match(r"^/api/quote/([^/]+)$", parsed_path)
    if quote_delete_match:
        handler._handle_quote_delete(quote_delete_match)
        return True

    document_delete_match = re.match(r"^/api/document/([^/]+)$", parsed_path)
    if document_delete_match:
        handler._handle_document_delete(document_delete_match)
        return True

    attachment_delete_match = re.match(r"^/api/email-attachment/([^/]+)$", parsed_path)
    if attachment_delete_match:
        handler._handle_email_attachment_delete(attachment_delete_match)
        return True

    email_delete_match = re.match(r"^/api/email/([^/]+)$", parsed_path)
    if email_delete_match:
        handler._handle_email_delete(email_delete_match)
        return True

    action_delete_match = re.match(r"^/api/actions/([^/]+)$", parsed_path)
    if action_delete_match:
        handler._handle_action_delete(action_delete_match)
        return True

    if parsed_path == '/api/imap/config':
        handler._handle_imap_config_delete()
        return True

    return False
