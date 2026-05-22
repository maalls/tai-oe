"""Tests for QuoteService._compute_document_totals."""

from service.quote.service import QuoteService


def test_compute_document_totals_applies_client_discount_and_tax():
    service = QuoteService(opportunity_repository=object())

    totals = service._compute_document_totals(
        [
            {
                "quantity": 2,
                "unit_price_excl_tax": 100,
                "tax_rate": 20,
                "client_discount_rate": 10,
            },
            {
                "quantity": 1,
                "unit_price_excl_tax": 50,
                "tax_rate": 10,
            },
        ]
    )

    assert totals == {
        "total_excl_tax": 230.0,
        "total_tax": 41.0,
        "total_incl_tax": 271.0,
    }


def test_compute_document_totals_handles_invalid_numbers_gracefully():
    service = QuoteService(opportunity_repository=object())

    totals = service._compute_document_totals(
        [
            {
                "quantity": "x",
                "unit_price_excl_tax": "y",
                "tax_rate": "z",
                "client_discount_rate": "bad",
            }
        ]
    )

    assert totals == {
        "total_excl_tax": 0.0,
        "total_tax": 0.0,
        "total_incl_tax": 0.0,
    }
