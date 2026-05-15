"""Filesystem path resolution helpers for legacy API server."""

from pathlib import Path

from src.api.routes.helpers.server_response_helpers import send_error


def resolve_fs_path(handler, current_file: str, raw_path: str):
    """Resolve a safe path under project root or send an error response."""
    if not raw_path:
        send_error(handler, 400, 'Missing path')
        return None

    base_dir = Path(current_file).resolve().parents[3]
    input_path = Path(raw_path)

    if raw_path.startswith('~'):
        raw_path = raw_path[1:].lstrip('/')
        input_path = Path(raw_path)

    if input_path.is_absolute():
        try:
            input_path = input_path.relative_to(base_dir)
        except Exception:
            send_error(handler, 400, 'Invalid path')
            return None

    target_path = (base_dir / input_path).resolve()

    if base_dir not in target_path.parents and target_path != base_dir:
        send_error(handler, 400, 'Invalid path')
        return None

    return target_path
