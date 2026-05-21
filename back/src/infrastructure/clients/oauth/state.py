"""Shared helpers for OAuth state encoding and decoding."""

import base64
import json
from typing import Any, Dict


def encode_oauth_state(payload: Dict[str, Any]) -> str:
    """Encode an OAuth state payload to URL-safe base64 JSON."""
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_oauth_state(state: str) -> Dict[str, Any]:
    """Decode OAuth state payload from URL-safe base64 JSON."""
    try:
        return json.loads(base64.urlsafe_b64decode(state.encode()).decode())
    except Exception:
        return {}
