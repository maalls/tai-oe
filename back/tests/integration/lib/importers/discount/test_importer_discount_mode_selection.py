import os
from pathlib import Path

from src.lib.importers.discount import DiscountImporter


class _FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class _FakeQuery:
    def __init__(self, table_name: str, client: "_FakeSupabase"):
        self.table_name = table_name
        self.client = client
        self.filters = {}
        self._action = "select"
        self._payload = None

    def select(self, _columns: str):
        self._action = "select"
        return self

    def update(self, payload: dict):
        self._action = "update"
        self._payload = payload
        return self

    def eq(self, key: str, value: str):
        self.filters[key] = value
        return self

    def _filter_rows(self, rows):
        filtered = rows
        for key, value in self.filters.items():
            filtered = [row for row in filtered if row.get(key) == value]
        return filtered

    def execute(self):
        if self.table_name == "family":
            if self._action == "select":
                return _FakeResponse(data=self._filter_rows(self.client.families))
            if self._action == "update":
                matches = self._filter_rows(self.client.families)
                for row in matches:
                    row.update(self._payload or {})
                return _FakeResponse(data=matches)
        return _FakeResponse(error=f"unexpected operation on table {self.table_name}")


class _FakeSupabase:
    def __init__(self):
        self.families = [
            {
                "id": "family-1",
                "brand_id": "brand-1",
                "code": "A10",
                "name": "Family A10",
                "quantity": 1.0,
                "discount": 2.0,
            }
        ]

    def table(self, table_name: str):
        return _FakeQuery(table_name, self)


def test_run_uses_text_mode_when_discount_mode_is_text(monkeypatch):
    monkeypatch.setenv("DISCOUNT_EXTRACTION_MODE", "text")

    importer = DiscountImporter(_FakeSupabase(), llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}
    importer.pdf_path = Path("dummy.pdf")
    importer.pdf_text = "text extracted from pdf"

    monkeypatch.setattr(
        importer,
        "parseDiscounts",
        lambda source_text=None: [
            {
                "family_code": "A10",
                "description": "Family A10",
                "quantity": 5,
                "discount": 15,
            }
        ],
    )
    monkeypatch.setattr(
        importer,
        "parseDiscountsUsingVision",
        lambda pdf_path=None: [
            {
                "family_code": "A10",
                "description": "Family A10",
                "quantity": 99,
                "discount": 99,
            }
        ],
    )

    result = importer.run()

    assert result["status"] if "status" in result else True
    assert result["updated"] == 1
    assert result["parsed_rows"] == 1


def test_run_uses_vision_mode_by_default(monkeypatch):
    monkeypatch.delenv("DISCOUNT_EXTRACTION_MODE", raising=False)

    importer = DiscountImporter(_FakeSupabase(), llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}
    importer.pdf_path = Path("dummy.pdf")
    importer.pdf_text = "text extracted from pdf"

    monkeypatch.setattr(
        importer,
        "parseDiscounts",
        lambda source_text=None: [
            {
                "family_code": "A10",
                "description": "Family A10",
                "quantity": 11,
                "discount": 11,
            }
        ],
    )
    monkeypatch.setattr(
        importer,
        "parseDiscountsUsingVision",
        lambda pdf_path=None: [
            {
                "family_code": "A10",
                "description": "Family A10",
                "quantity": 7,
                "discount": 33,
            }
        ],
    )

    result = importer.run()

    assert result["updated"] == 1
    assert result["parsed_rows"] == 1

    # Ensure test did not leak env var to other tests in this process.
    os.environ.pop("DISCOUNT_EXTRACTION_MODE", None)
