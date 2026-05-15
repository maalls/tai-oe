"""Core POST route dispatch for legacy API server."""

from src.api.routes.server_post_utility_handlers import (
    handle_curl_post,
    handle_fs_create_post,
    handle_fs_read_post,
    handle_products_post,
)


def dispatch_post_core_routes(handler, parsed_path: str) -> bool:
    """Dispatch core POST routes and return True when handled."""
    if parsed_path == '/api/products':
        handle_products_post(handler)
        return True

    if parsed_path == '/api/fs/create':
        handle_fs_create_post(handler)
        return True

    if parsed_path == '/api/fs/read':
        handle_fs_read_post(handler)
        return True

    if parsed_path == '/api/curl':
        handle_curl_post(handler)
        return True

    return False
