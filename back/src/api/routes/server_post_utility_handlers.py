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
