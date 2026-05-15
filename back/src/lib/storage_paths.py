"""Shared storage path helpers."""

from pathlib import Path


_SOURCE_MAP = {
    "rfp_upload": "rfp_uploads",
    "email": "emails",
    "quote": "quotes",
    "invoice": "invoices",
    "attachment": "attachments",
}


def get_storage_dir(source: str) -> Path:
    """Return the storage directory for a logical source."""
    base_storage = Path("var/storage")
    subdir = _SOURCE_MAP.get(source, source)
    return base_storage / subdir


def get_storage_path(source: str, filename: str) -> Path:
    """Return the full storage path for a source and filename."""
    return get_storage_dir(source) / filename
