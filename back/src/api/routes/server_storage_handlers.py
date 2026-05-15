"""Compatibility facade for storage HEAD/GET handlers."""

from src.api.file.handler import (
    handle_storage_get,
    handle_storage_head,
)

__all__ = [
    "handle_storage_head",
    "handle_storage_get",
]
