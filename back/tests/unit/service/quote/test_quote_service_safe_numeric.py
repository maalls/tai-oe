"""Tests for QuoteService.safe_numeric."""

from service.quote.service import QuoteService


def test_safe_numeric_returns_float_for_numeric_values():
    service = QuoteService(opportunity_repository=object())

    assert service.safe_numeric("12.5") == 12.5
    assert service.safe_numeric(7) == 7.0


def test_safe_numeric_returns_zero_for_invalid_values_by_default():
    service = QuoteService(opportunity_repository=object())

    assert service.safe_numeric(None) == 0
    assert service.safe_numeric("not-a-number") == 0


def test_safe_numeric_honors_custom_default():
    service = QuoteService(opportunity_repository=object())

    assert service.safe_numeric(None, default=1.5) == 1.5
