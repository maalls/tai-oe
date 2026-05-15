"""Tests for QuoteService.safe_numeric."""

from service.quote.service import QuoteService


def test_safe_numeric_returns_float_for_numeric_values():
    service = QuoteService(supabase=object(), opportunity_repository=object())

    assert service.safe_numeric("12.5") == 12.5
    assert service.safe_numeric(7) == 7.0


def test_safe_numeric_returns_none_for_invalid_values():
    service = QuoteService(supabase=object(), opportunity_repository=object())

    assert service.safe_numeric(None) is None
    assert service.safe_numeric("not-a-number") is None
