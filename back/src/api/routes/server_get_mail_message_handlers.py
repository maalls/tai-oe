"""Detailed Gmail message GET handlers for legacy API server."""

from src.config import EMAIL_FETCH_MAX_RESULTS


def handle_gmail_messages_get(handler, qs):
    """Handle /api/gmail/messages GET endpoint."""
    request_handlers = handler.get_request_handlers()
    max_results = handler._get_qs_int(qs, 'max_results', EMAIL_FETCH_MAX_RESULTS)
    user_id = qs.get('user_id', [None])[0]
    force = handler._get_qs_bool(qs, 'force', False)

    print(f"[RAG] /api/gmail/messages - user_id from query: {user_id}, force: {force}")

    if not user_id:
        auth_header = handler.headers.get('Authorization', '')
        print(f"[RAG] Auth header: {auth_header[:50] if auth_header else 'None'}...")
        user_id = handler._get_optional_user_id_from_auth(auth_header)
        print(f"[RAG] Extracted user_id from token: {user_id}")

    print(f"[RAG] Final user_id: {user_id}")
    if not user_id:
        return handler._send_error(400, 'Missing user_id')

    result = request_handlers.handle_gmail_list_messages(
        max_results=max_results,
        user_id=user_id,
        save_to_db=True,
        force=force,
    )
    return handler.json(result)


def handle_gmail_classify_unclassified_get(handler, qs):
    """Handle /api/gmail/classify-unclassified GET endpoint."""
    request_handlers = handler.get_request_handlers()
    user_id = qs.get('user_id', [None])[0]
    limit = handler._get_qs_int(qs, 'limit', 200)

    if not user_id:
        auth_header = handler.headers.get('Authorization', '')
        user_id = handler._get_optional_user_id_from_auth(auth_header)

    if not user_id:
        return handler._send_error(400, 'Missing user_id')

    result = request_handlers.handle_classify_unclassified(user_id=user_id, limit=limit)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_gmail_message_get(handler, parsed_path: str):
    """Handle /api/gmail/message/<id> GET endpoint."""
    message_id = parsed_path.split('/api/gmail/message/')[-1]
    auth_header = handler.headers.get('Authorization', '')
    print(f"[RAG] /api/gmail/message/{message_id} - Auth header: {auth_header[:50] if auth_header else 'None'}...")
    user_id = handler._get_optional_user_id_from_auth(auth_header)
    print(f"[RAG] Extracted user_id from token: {user_id}")
    print(f"[RAG] Final user_id for message body: {user_id}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_message_body(message_id, user_id)
    return handler.json(result)


def handle_email_attachment_get(handler, parsed_path: str):
    """Handle /api/email-attachment/<id> GET endpoint."""
    attachment_id = parsed_path.split('/api/email-attachment/')[-1].split('/')[0]
    auth_header = handler.headers.get('Authorization', '')
    user_id = handler._get_optional_user_id_from_auth(auth_header)

    request_handlers = handler.get_request_handlers()
    status_code, headers, file_content = request_handlers.handle_email_attachment_download(attachment_id, user_id)

    handler.send_response(status_code)
    for header_name, header_value in headers.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()
    handler.wfile.write(file_content)
    return None
