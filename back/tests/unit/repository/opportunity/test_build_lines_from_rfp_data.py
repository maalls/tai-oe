"""Tests for OpportunityRepository._build_lines_from_rfp_data."""

from src.repository.opportunity import OpportunityRepository


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, table_name: str, datasets: dict):
        self.table_name = table_name
        self.datasets = datasets

    def select(self, _fields):
        return self

    def in_(self, _field, _values):
        return self

    def ilike(self, _field, _value):
        return self

    def execute(self):
        return _Response(self.datasets.get(self.table_name, []))


class _Supabase:
    def __init__(self, datasets: dict):
        self.datasets = datasets

    def table(self, table_name: str):
        return _Query(table_name, self.datasets)


def test_build_lines_uses_catalog_price_when_extracted_price_is_zero():
    repo = OpportunityRepository()
    supabase = _Supabase(
        {
            "product": [
                {
                    "sku": "SKU-1",
                    "price": 50,
                    "brand": {"target_margin": 0},
                    "product_family": [],
                }
            ],
            "family": [],
        }
    )

    rfp_data = {
        "products": [
            {
                "sku": "SKU-1",
                "quantity": 2,
                "price": 0,
                "tax_rate": 20,
                "description": "Line 1",
                "manufacturer": "ABB",
            }
        ]
    }

    lines, totals = repo._build_lines_from_rfp_data(rfp_data, supabase)

    assert lines[0]["unit_price_excl_tax"] == 50
    assert lines[0]["line_total_excl_tax"] == 100
    assert totals["total_excl_tax"] == 100
    assert totals["total_tax"] == 20
    assert totals["total_incl_tax"] == 120
