"""Query-string and payload parsing helpers for legacy API server."""


def get_qs_int(qs, key: str, default: int) -> int:
    """Read integer query-string parameter with fallback."""
    try:
        return int(qs.get(key, [default])[0])
    except Exception:
        return default


def get_qs_value(qs, key: str, default=None):
    """Read first query-string value with fallback."""
    return qs.get(key, [default])[0]


def get_payload_int(payload: dict, key: str, default: int) -> int:
    """Read integer payload value with fallback."""
    try:
        return int(payload.get(key) or default)
    except Exception:
        return default


def get_qs_bool(qs, key: str, default: bool = False) -> bool:
    """Read boolean query-string parameter with fallback."""
    raw_value = qs.get(key, [None])[0]
    if raw_value is None:
        return default
    return str(raw_value).strip().lower() in ('1', 'true', 'yes', 'on')
