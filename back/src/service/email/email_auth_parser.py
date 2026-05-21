"""Compatibility wrapper for email auth parser.

Canonical implementation is in src.lib.email.auth_parser.
"""

from src.lib.email.auth_parser import EmailAuthParser, parse_email_auth

__all__ = ["EmailAuthParser", "parse_email_auth"]
