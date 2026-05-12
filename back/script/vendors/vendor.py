"""Vendor handler utilities."""

from __future__ import annotations

from typing import Any, Dict


def handle_vendor(config: Dict[str, Any]) -> None:
    """Handle a vendor using its config dictionary."""
    vendor_name = config.get("name") or "unknown"
    vendor_type = config.get("type") or "unknown"
    file_path = config.get("file_path")
    csv_output_dir = config.get("csv_output_dir")

    print(
        f"Handling vendor '{vendor_name}' (type={vendor_type}) file_path={file_path} csv_output_dir={csv_output_dir}"
    )
