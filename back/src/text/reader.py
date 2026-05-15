"""Backward-compatible shim — real implementation in src.lib.extractors.text_reader."""
from src.lib.extractors.text_reader import (
    extract_rfp_from_email,
    extract_company_from_text,
    extract_rfp_from_text,
)
__all__ = ["extract_rfp_from_email", "extract_company_from_text", "extract_rfp_from_text"]
