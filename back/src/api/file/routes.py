"""Domain router for file/storage endpoints."""

from src.api.file.handler import (
    handle_curl_post,
    handle_fetch_get,
    handle_fs_create_post,
    handle_fs_read_post,
    handle_storage_get,
    handle_storage_head,
)


def dispatch_file_routes(handler, method: str, parsed, qs, _request_handlers) -> bool:
    """Dispatch file/storage routes across HTTP methods and return True when handled."""
    path = parsed.path

    if method == "GET":
        if path == '/api/fetch':
            handle_fetch_get(handler, qs)
            return True

        if path.startswith('/api/storage/'):
            handle_storage_get(handler, handler.config['STORAGE_DIR'], path)
            return True

        return False

    if method == "HEAD":
        if path.startswith('/api/storage/'):
            handle_storage_head(handler, handler.config['STORAGE_DIR'], path)
            return True

        return False

    if method == "POST":
        if path == '/api/fs/create':
            handle_fs_create_post(handler)
            return True

        if path == '/api/fs/read':
            handle_fs_read_post(handler)
            return True

        if path == '/api/curl':
            handle_curl_post(handler)
            return True

        return False

    return False
