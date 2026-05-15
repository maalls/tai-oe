"""Core POST route dispatch for legacy API server."""


def dispatch_post_core_routes(handler, parsed_path: str) -> bool:
    """Dispatch core POST routes and return True when handled."""
    if parsed_path == '/api/products':
        handler._handle_products_post()
        return True

    if parsed_path == '/api/fs/create':
        handler._handle_fs_create_post()
        return True

    if parsed_path == '/api/fs/read':
        handler._handle_fs_read_post()
        return True

    if parsed_path == '/api/curl':
        handler._handle_curl_post()
        return True

    return False
