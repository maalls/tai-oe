from pathlib import Path

import pytest

from src.lib.importers.discount import DiscountImporter


class FakeResponse:
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error


class FakeQuery:
    def __init__(self, table_name: str, client: "FakeSupabaseClient"):
        self.table_name = table_name
        self.client = client
        self.filters = {}
        self._action = "select"
        self._payload = None

    def select(self, _columns: str) -> "FakeQuery":
        self._action = "select"
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self._action = "update"
        self._payload = payload
        return self

    def eq(self, key: str, value: str) -> "FakeQuery":
        self.filters[key] = value
        return self

    def _filter_rows(self, rows: list[dict]) -> list[dict]:
        filtered = rows
        for key, value in self.filters.items():
            filtered = [row for row in filtered if row.get(key) == value]
        return filtered

    def execute(self) -> FakeResponse:
        if self.client.query_error:
            return FakeResponse(error=self.client.query_error)

        if self.table_name == "brand":
            if self._action != "select":
                return FakeResponse(error="unsupported action for brand table")
            return FakeResponse(data=self._filter_rows(self.client.brands))

        if self.table_name == "family":
            if self._action == "select":
                return FakeResponse(data=self._filter_rows(self.client.families))

            if self._action == "update":
                matches = self._filter_rows(self.client.families)
                for row in matches:
                    row.update(self._payload or {})
                    self.client.updated_families.append(dict(row))
                return FakeResponse(data=matches)

            return FakeResponse(error=f"unsupported action for family table: {self._action}")

        return FakeResponse(error=f"unexpected table: {self.table_name}")


class FakeSupabaseClient:
    def __init__(self):
        self.query_error = None
        self.brands = [
            {
                "id": "brand-1",
                "name": "ABB",
                "marque": "ABB",
                "vendor_id": "vendor-1",
            }
        ]
        self.families = []
        self.updated_families = []

    def table(self, table_name: str) -> FakeQuery:
        return FakeQuery(table_name, self)


class FakeLLMClient:
    def __init__(self, response):
        self.response = response

    def ask_json(self, **_kwargs):
        return self.response


def test_set_brand_sets_brand_when_found() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())

    brand = importer.setBrand("ABB")

    assert brand["id"] == "brand-1"
    assert importer.brand == brand


def test_set_brand_raises_when_brand_not_found() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())

    with pytest.raises(ValueError, match="Brand not found"):
        importer.setBrand("ABC")


def test_load_pdf_reads_text_from_asset() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())
    asset_path = Path(__file__).resolve().parents[1] / "assets" / "test_asset_abb_2026.pdf"

    if not asset_path.exists():
        pytest.skip(f"Missing shared test asset: {asset_path}")

    text = importer.load_pdf(asset_path)

    assert isinstance(text, str)
    assert len(text) > 0
    assert importer.pdf_path == asset_path
    assert importer.pdf_text == text


def test_parse_discounts_normalizes_llm_family_rows() -> None:
    llm_response = {
        "families": [
            {
                "familyCode": "A9",
                "description": "Modules de protection",
                "quantity": "10",
                "discountRate": "12,5%",
            }
        ]
    }

    importer = DiscountImporter(FakeSupabaseClient(), llm_client=FakeLLMClient(llm_response))
    rows = importer.parseDiscounts("sample extracted text")

    assert len(rows) == 1
    assert rows[0]["family_code"] == "A9"
    assert rows[0]["description"] == "Modules de protection"
    assert rows[0]["quantity"] == 10.0
    assert rows[0]["discount"] == 12.5


def test_parse_discounts_using_vision_requires_vision_capable_llm() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())
    asset_path = Path(__file__).resolve().parents[1] / "assets" / "test_asset_abb_2026.pdf"

    if not asset_path.exists():
        pytest.skip(f"Missing shared test asset: {asset_path}")

    with pytest.raises(RuntimeError, match="does not support vision"):
        importer.parseDiscountsUsingVision(asset_path)


def test_upsert_discount_updates_family_by_code_first() -> None:
    client = FakeSupabaseClient()
    client.families = [
        {"id": "f-1", "brand_id": "brand-1", "code": "A10", "name": "Old Name", "quantity": 1.0, "discount": 2.0}
    ]

    importer = DiscountImporter(client, llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    summary = importer.upsertDiscount(
        [{"family_code": "A10", "description": "Other Name", "quantity": 12, "discount": 42.5}]
    )

    assert summary["updated"] == 1
    assert summary["skipped"] == 0
    assert client.families[0]["quantity"] == 12.0
    assert client.families[0]["discount"] == 42.5


def test_upsert_discount_falls_back_to_description_when_code_not_found() -> None:
    client = FakeSupabaseClient()
    client.families = [
        {"id": "f-1", "brand_id": "brand-1", "code": "A11", "name": "Modules de protection", "quantity": 1.0, "discount": 2.0}
    ]

    importer = DiscountImporter(client, llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    summary = importer.upsertDiscount(
        [{"family_code": "UNKNOWN", "description": "Modules de protection", "quantity": 5, "discount": 9.5}]
    )

    assert summary["updated"] == 1
    assert summary["skipped"] == 0
    assert client.families[0]["quantity"] == 5.0
    assert client.families[0]["discount"] == 9.5


def test_upsert_discount_skips_missing_when_flag_enabled() -> None:
    client = FakeSupabaseClient()
    client.families = [
        {"id": "f-1", "brand_id": "brand-1", "code": "A11", "name": "Known", "quantity": 1.0, "discount": 2.0}
    ]

    importer = DiscountImporter(client, llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    summary = importer.upsertDiscount(
        [{"family_code": "NOPE", "description": "Missing", "quantity": 1, "discount": 2}],
        skip_missing=True,
    )

    assert summary["updated"] == 0
    assert summary["skipped"] == 1
    assert len(summary["skipped_rows"]) == 1


def test_upsert_discount_skips_null_discount_when_flag_enabled() -> None:
    client = FakeSupabaseClient()
    client.families = [
        {"id": "f-1", "brand_id": "brand-1", "code": "A10", "name": "Family A10", "quantity": 1.0, "discount": 2.0}
    ]

    importer = DiscountImporter(client, llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    summary = importer.upsertDiscount(
        [{"family_code": "A10", "description": "Family A10", "quantity": 1, "discount": None}],
        skip_missing=True,
    )

    assert summary["updated"] == 0
    assert summary["skipped"] == 1
    assert summary["skipped_rows"][0]["reason"] == "missing discount"


def test_upsert_discount_raises_on_null_discount_when_skip_disabled() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    with pytest.raises(ValueError, match="Missing discount"):
        importer.upsertDiscount(
            [{"family_code": "A10", "description": "Family A10", "quantity": 1, "discount": None}],
            skip_missing=False,
        )


def test_upsert_discount_raises_when_missing_and_skip_disabled() -> None:
    importer = DiscountImporter(FakeSupabaseClient(), llm_client=object())
    importer.brand = {"id": "brand-1", "name": "ABB"}

    with pytest.raises(ValueError, match="No matching family found"):
        importer.upsertDiscount(
            [{"family_code": "NOPE", "description": "Missing", "quantity": 1, "discount": 2}],
            skip_missing=False,
        )


def test_run_parses_and_updates_discounts(monkeypatch) -> None:
    client = FakeSupabaseClient()
    client.families = [
        {"id": "f-1", "brand_id": "brand-1", "code": "A10", "name": "Family A10", "quantity": 1.0, "discount": 2.0}
    ]
    llm_response = {
        "families": [
            {
                "family_code": "A10",
                "description": "Family A10",
                "quantity": 3,
                "discount": 77,
            }
        ]
    }

    importer = DiscountImporter(client, llm_client=FakeLLMClient(llm_response))
    importer.brand = {"id": "brand-1", "name": "ABB"}
    importer.pdf_path = Path("dummy.pdf")
    importer.pdf_text = "sample extracted text"
    monkeypatch.setattr(importer, "parseDiscountsUsingVision", lambda pdf_path=None: [
        {
            "family_code": "A10",
            "description": "Family A10",
            "quantity": 3,
            "discount": 77,
        }
    ])

    summary = importer.run()

    assert summary["brand_id"] == "brand-1"
    assert summary["brand_name"] == "ABB"
    assert summary["parsed_rows"] == 1
    assert summary["rows"] == 1
    assert summary["updated"] == 1
    assert summary["skipped"] == 0
    assert client.families[0]["quantity"] == 3.0
    assert client.families[0]["discount"] == 77.0
