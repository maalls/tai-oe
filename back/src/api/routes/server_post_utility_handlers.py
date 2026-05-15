"""Utility POST handlers for legacy API server."""


def handle_products_post(handler):
    """Handle /api/products POST endpoint."""
    payload = handler._read_json(default={})
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_product(payload)
    return handler.json(result, 201)


def handle_fs_create_post(handler):
    """Handle /api/fs/create POST endpoint."""
    payload = handler._read_json(default={})
    raw_path = str(payload.get('path') or '').strip()
    kind = payload.get('type') or 'dir'

    target_path = handler._resolve_fs_path(raw_path)
    if target_path is None:
        return None

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fs_create(target_path=target_path, kind=kind)
    except Exception as e:
        return handler._send_error(500, f'Create failed: {e}')
    return handler.json(result)


def handle_fs_read_post(handler):
    """Handle /api/fs/read POST endpoint."""
    payload = handler._read_json(default={})
    raw_path = str(payload.get('path') or '').strip()

    max_chars = handler._get_payload_int(payload, 'max_chars', 10000)
    max_chars = max(100, min(max_chars, 50000))

    target_path = handler._resolve_fs_path(raw_path)
    if target_path is None:
        return None

    if not target_path.exists() or not target_path.is_file():
        return handler._send_error(404, 'File not found')

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_fs_read(target_path=target_path, max_chars=max_chars)
    except Exception as e:
        return handler._send_error(500, f'Read failed: {e}')
    return handler.json(result)


def handle_curl_post(handler):
    """Handle /api/curl POST endpoint."""
    payload = handler._read_json(default={})

    target_url = str(payload.get('url') or '').strip()
    if not target_url:
        return handler._send_error(400, 'Missing url')
    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        return handler._send_error(400, 'Invalid url scheme')

    method = str(payload.get('method') or 'GET').upper()
    if method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        return handler._send_error(400, 'Invalid method')

    headers = payload.get('headers') if isinstance(payload.get('headers'), dict) else {}
    body_text = payload.get('body') if isinstance(payload.get('body'), str) else None

    max_chars = handler._get_payload_int(payload, 'max_chars', 10000)
    timeout_ms = handler._get_payload_int(payload, 'timeout_ms', 8000)

    max_chars = max(100, min(max_chars, 50000))
    timeout_ms = max(1000, min(timeout_ms, 20000))

    try:
        request_handlers = handler.get_request_handlers()
        result = request_handlers.handle_curl_request(
            target_url=target_url,
            method=method,
            headers=headers,
            body_text=body_text,
            max_chars=max_chars,
            timeout_ms=timeout_ms,
        )
        return handler.json(result)
    except Exception as e:
        return handler._send_error(500, f'Curl failed: {e}')


def handle_auth_signup_post(handler):
    """Handle /api/auth/signup POST endpoint."""
    body = handler._read_body()
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_signup(body)
    status = handler._pop_status(result)
    return handler.json(result, status)


def handle_auth_login_post(handler):
    """Handle /api/auth/login POST endpoint."""
    body = handler._read_body()
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_login(body)
    status = handler._pop_status(result)
    return handler.json(result, status)


def handle_auth_logout_post(handler):
    """Handle /api/auth/logout POST endpoint."""
    auth_header = handler.headers.get('Authorization', '')
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_auth_logout(auth_header)
    status = handler._pop_status(result)
    return handler.json(result, status)


def handle_entity_update_post(handler, entity_update_match):
    """Handle /api/entity/{table}/{field} POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    table = entity_update_match.group(1)
    field = entity_update_match.group(2)

    payload = handler._read_json(default={})

    record_id = payload.get('id') or payload.get('record_id')
    if record_id is None:
        return handler.json({"status": "error", "message": "Missing id"}, 400)

    if 'value' not in payload:
        return handler.json({"status": "error", "message": "Missing value"}, 400)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_update_entity_field(
        table=table,
        field=field,
        record_id=record_id,
        value=payload.get('value'),
        user_id=user_id,
    )
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_emails_classify_post(handler, parsed_path):
    """Handle /api/emails/classify/{email_uuid} POST endpoint."""
    email_uuid = parsed_path.split('/')[-1]

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id')
    print(f"[RAG] Classify request for email {email_uuid} by user {user_id}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_classify_email(email_uuid=email_uuid, user_id=user_id, force=True)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_rfq_generate_post(handler):
    """Handle /api/rfq/generate POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    payload = handler._read_json(default={})

    text = payload.get('text') or payload.get('content')
    message_id = payload.get('message_id')

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_rfq_generate(text=text, message_id=message_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_opportunities_create_from_email_post(handler):
    """Handle /api/opportunities/create-from-email POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    payload = handler._read_json(default={})

    message_id = payload.get('message_id')
    if not message_id:
        return handler.json({"error": "Missing message_id parameter"}, 400)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_from_email(message_id=message_id, user_id=user_id)
    print(f"[RAG] Create opportunity result: {result.get('status')}, {result}")
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_opportunities_create_manual_post(handler):
    """Handle /api/opportunities/create-manual POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    payload = handler._read_json(default={})

    name = payload.get('name')
    if not name:
        return handler.json({"status": "error", "message": "Missing name parameter"}, 400)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_manual(user_id=user_id, name=name)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_opportunities_create_from_rfp_post(handler):
    """Handle /api/opportunities/create-from-rfp POST endpoint."""
    body = handler._read_body()
    content_type = handler.headers.get('Content-Type', '')

    auth_header = handler.headers.get('Authorization', '')
    print(f"[RAG] Auth header present: {bool(auth_header)}, header: {auth_header[:50] if auth_header else 'None'}")
    user_data = handler._require_auth(auth_header=auth_header)
    print(f"[RAG] Token valid: {bool(user_data)}, user_data: {user_data}")
    if user_data is None:
        print(f"[RAG] Authorization failed for token: {auth_header[:50] if auth_header else 'None'}")
        return None

    user_id = user_data.get('id') if user_data else None
    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_create_opportunity_from_rfp(body=body, content_type=content_type, user_id=user_id)
    print(f"[RAG] Create opportunity from RFP result: {result.get('status')}")
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_extract_contact_post(handler):
    """Handle /api/email/extract-contact POST endpoint."""
    payload = handler._read_json(default={})

    email_id = payload.get('email_id')
    email_body = payload.get('email_body')

    if not email_body:
        return handler.json({"error": "Missing email_body parameter"}, 400)

    auth_header = handler.headers.get('Authorization', '')
    user_data = handler._require_auth(auth_header=auth_header, required=False)
    user_id = user_data.get('id') if user_data else None
    print(f"[RAG] Extract contact - Auth valid: {bool(user_data)}, user_id: {user_id}, auth_header: {auth_header[:50]}")

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_extract_contact_from_email(email_id=email_id, email_body=email_body, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_auth_status_post(handler, parsed_path):
    """Handle /api/email/auth/{email_id} POST endpoint."""
    email_id = parsed_path.split('/api/email/auth/')[-1]

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_email_auth_status(email_id=email_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_resync_post(handler, parsed_path):
    """Handle /api/email/{email_id}/resync POST endpoint."""
    path_parts = parsed_path.split('/')
    email_id = path_parts[-2] if len(path_parts) >= 4 else None

    if not email_id:
        return handler.json({"error": "Missing email_id"}, 400)

    payload = handler._read_json(default={})
    provider_message_id = payload.get('provider_message_id')
    if not provider_message_id:
        return handler.json({"error": "Missing provider_message_id"}, 400)

    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_email_resync(email_id=email_id, provider_message_id=provider_message_id, user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_senders_high_risk_post(handler):
    """Handle /api/email/senders/high-risk POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_high_risk_senders(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)


def handle_email_senders_verified_post(handler):
    """Handle /api/email/senders/verified POST endpoint."""
    user_data = handler._require_auth()
    if user_data is None:
        return None

    user_id = user_data.get('id') if user_data else None
    if not user_id:
        return handler.json({"error": "Unauthorized"}, 401)

    request_handlers = handler.get_request_handlers()
    result = request_handlers.handle_get_verified_senders(user_id=user_id)
    status = handler._status_from_result(result)
    return handler.json(result, status)
