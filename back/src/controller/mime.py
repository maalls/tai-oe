import re
from email.header import decode_header, make_header
from email.utils import parseaddr

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def decode_mime_words(s: str) -> str:
    """Decode strings like '=?UTF-8?B?...?=' into readable unicode."""
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s))).strip()
    except Exception:
        # Fallback: return as-is
        return s.strip()

def normalize_email(addr: str) -> str:
    """Lowercase + strip. (Email local-part can be case-sensitive in theory,
    but in practice lowercasing is usually what you want for dedupe.)"""
    addr = (addr or "").strip()
    return addr.lower()

def parse_from_header(from_header: str):
    """
    Returns: (from_email, from_name, from_domain, from_raw, is_valid)
    """
    raw = from_header or ""
    name, email_addr = parseaddr(raw)  # handles 'Name <email>' and variants

    name = decode_mime_words(name)
    email_addr = normalize_email(email_addr)

    domain = ""
    if "@" in email_addr:
        domain = email_addr.split("@", 1)[1]

    is_valid = bool(email_addr) and bool(EMAIL_RE.match(email_addr))
    return email_addr, name, domain, raw, is_valid
