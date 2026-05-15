"""DELETE handlers for legacy API server."""

import sys


def handle_imap_config_delete(handler):
    """Handle DELETE /api/imap/config."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_imap_config_delete(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_action_delete(handler, action_delete_match):
    """Handle DELETE /api/actions/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    action_id = action_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_delete_action(action_id=action_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_delete(handler, email_delete_match):
    """Handle DELETE /api/email/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    email_id = email_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_delete(email_id=email_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_attachment_delete(handler, attachment_delete_match):
    """Handle DELETE /api/email-attachment/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    attachment_id = attachment_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_attachment_delete(attachment_id=attachment_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_document_delete(handler, document_delete_match):
    """Handle DELETE /api/document/{id}."""
    user_id = handler._require_auth_user_id()
    if user_id is None:
        return None

    document_id = document_delete_match.group(1)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_delete_document(document_id=document_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)
