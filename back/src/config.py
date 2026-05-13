"""Vendor configuration loader sourced from config.yml."""

import os
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError("Missing dependency: PyYAML. Install with: pip install PyYAML") from exc


def get_int_env(name: str, default: int) -> int:
    """Read an integer environment variable with fallback."""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


EMAIL_FETCH_MAX_RESULTS = get_int_env("EMAIL_FETCH_MAX_RESULTS", 50)


def _find_config() -> Path:
    """Locate config.yml in common locations."""

    current_dir = Path(__file__).resolve().parents[1]
    candidates = [
        current_dir / "config.yml",
        Path.cwd() / "config.yml",
        Path.cwd() / "back" / "config.yml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError("config.yml not found. Please place it at back/config.yml or pass an absolute path.")


def get_vendor_config(vendor: str, config_path: Optional[Path] = None) -> Dict:
    """Load configuration for a specific vendor from config.yml."""

    path = config_path or _find_config()
    with path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    app_config = config.get("app", {})
    vendor_config = app_config.get("vendor", {})
    specific_vendor_config = vendor_config.get(vendor, {})

    if not specific_vendor_config:
        print(f"⚠️  No config found for vendor '{vendor}' in {path}")
        print(f"   Available vendors: {list(vendor_config.keys())}")

    return specific_vendor_config
