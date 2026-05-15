import pytest
from pathlib import Path
from src.lib.importers.net_price import NetPriceImporter

class FakeResponse:
	def __init__(self, data=None, error=None):
		self.data = data or []
		self.error = error

class FakeQuery:
	def __init__(self, table_name: str, client: "FakeSupabaseClient"):
		self.table_name = table_name
		self.client = client
		self.filters = {}
		self._limit = None
		self._action = "select"
		self._payload = None

	def select(self, _columns: str) -> "FakeQuery":
		self._action = "select"
		return self

	def insert(self, payload: dict) -> "FakeQuery":
		self._action = "insert"
		self._payload = payload
		return self

	def update(self, payload: dict) -> "FakeQuery":
		self._action = "update"
		self._payload = payload
		return self

	def delete(self) -> "FakeQuery":
		self._action = "delete"
		return self

	def eq(self, key: str, value: str) -> "FakeQuery":
		self.filters[key] = value
		return self

	def limit(self, value: int) -> "FakeQuery":
		self._limit = value
		return self

	def _filter_rows(self, rows: list[dict]) -> list[dict]:
		filtered = rows
		for key, value in self.filters.items():
			filtered = [row for row in filtered if row.get(key) == value]
		if self._limit is not None:
			filtered = filtered[: self._limit]
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

			if self._action == "insert":
				new_row = dict(self._payload or {})
				new_row["id"] = f"family-{len(self.client.families) + 1}"
				self.client.families.append(new_row)
				self.client.inserted_families.append(new_row)
				return FakeResponse(data=[new_row])

			if self._action == "update":
				matches = self._filter_rows(self.client.families)
				for row in matches:
					row.update(self._payload or {})
					self.client.updated_families.append(dict(row))
				return FakeResponse(data=matches)

			if self._action == "delete":
				matches = self._filter_rows(self.client.families)
				match_ids = {row.get("id") for row in matches}
				self.client.families = [
					row for row in self.client.families if row.get("id") not in match_ids
				]
				self.client.deleted_families.extend(matches)
				return FakeResponse(data=matches)

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
		self.inserted_families = []
		self.updated_families = []
		self.deleted_families = []

	def table(self, table_name: str) -> FakeQuery:
		return FakeQuery(table_name, self)


class FakeLLMClient:
	def __init__(self, response):
		self.response = response

	def ask_json(self, **_kwargs):
		return self.response


def test_set_brand_sets_brand_when_found() -> None:
	importer = NetPriceImporter(FakeSupabaseClient(), llm_client=object())

	brand = importer.setBrand("ABB")

	assert brand["id"] == "brand-1"
	assert importer.brand == brand


def test_set_brand_raises_when_brand_not_found() -> None:
	importer = NetPriceImporter(FakeSupabaseClient(), llm_client=object())

	with pytest.raises(ValueError, match="Brand not found"):
		importer.setBrand("ABC")


def test_load_pdf_reads_text_from_asset() -> None:
	importer = NetPriceImporter(FakeSupabaseClient(), llm_client=object())
	asset_path = Path(__file__).resolve().parents[4] / "fixtures" / "files" / "net_price" / "test_asset_abb_2026.pdf"

	text = importer.load_pdf(asset_path)

	assert asset_path.exists()
	assert isinstance(text, str)
	assert len(text) > 0
	assert importer.pdf_path == asset_path
	assert importer.pdf_text == text


def test_parse_net_prices_normalizes_llm_product_rows() -> None:
	llm_response = {
		"products": [
			{
				"productCode": "2CDS251001R0164",
				"local_code": "F15125",
				"description": "S200 M C16",
				"quantity": "10",
				"netPrice": "12,34",
			}
		]
	}
	importer = NetPriceImporter(FakeSupabaseClient(), llm_client=FakeLLMClient(llm_response))

	rows = importer.parseNetPrices("sample extracted text")

	assert len(rows) == 1
	assert rows[0]["product_code"] == "2CDS251001R0164"
	assert rows[0]["local_code"] == "F15125"
	assert rows[0]["description"] == "S200 M C16"
	assert rows[0]["quantity"] == 10.0
	assert rows[0]["net_price"] == 12.34


def test_upsert_net_prices_replaces_existing_family_entries() -> None:
	client = FakeSupabaseClient()
	client.families = [
		{
			"id": "family-existing",
			"brand_id": "brand-1",
			"type": "net_price",
			"product_code": "470136",
			"name": "old",
			"quantity": 1.0,
			"net_price": 1.0,
		}
	]

	importer = NetPriceImporter(client, llm_client=object())
	importer.brand = {"id": "brand-1", "name": "ABB"}

	result = importer.upsertNetPrices(
		[
			{
				"product_code": "470136",
				"description": "DISJ. PH/N SN201T-C10 U / 3KA",
				"quantity": 72,
				"net_price": 3.91,
			},
			{
				"product_code": "470138",
				"description": "DISJ. PH/N SN201T-C16 U / 3KA",
				"quantity": 72,
				"net_price": 3.91,
			},
		]
	)

	assert result == {"rows": 2, "deleted": 1, "created": 2, "updated": 0, "skipped": 0}
	assert any(f["id"] == "family-existing" for f in client.deleted_families)
	assert len(client.families) == 2
	assert any(f["product_code"] == "470138" for f in client.inserted_families)
	recreated = next(f for f in client.families if f["product_code"] == "470136")
	assert recreated["quantity"] == 72
	assert recreated["net_price"] == 3.91


def test_upsert_net_prices_raises_without_product_code() -> None:
	client = FakeSupabaseClient()
	importer = NetPriceImporter(client, llm_client=object())
	importer.brand = {"id": "brand-1", "name": "ABB"}

	with pytest.raises(ValueError, match="Missing product_code"):
		importer.upsertNetPrices(
			[
				{"product_code": "", "quantity": 2, "net_price": 1.5},
			]
		)


def test_upsert_net_prices_raises_without_quantity() -> None:
	client = FakeSupabaseClient()
	importer = NetPriceImporter(client, llm_client=object())
	importer.brand = {"id": "brand-1", "name": "ABB"}

	with pytest.raises(ValueError, match="Missing quantity"):
		importer.upsertNetPrices(
			[
				{"product_code": "470136", "quantity": None, "net_price": 1.5},
			]
		)


def test_upsert_net_prices_raises_without_net_price() -> None:
	client = FakeSupabaseClient()
	importer = NetPriceImporter(client, llm_client=object())
	importer.brand = {"id": "brand-1", "name": "ABB"}

	with pytest.raises(ValueError, match="Missing net_price"):
		importer.upsertNetPrices(
			[
				{"product_code": "470136", "quantity": 2, "net_price": None},
			]
		)


def test_run_parses_and_upserts_net_prices() -> None:
	client = FakeSupabaseClient()
	llm_response = {
		"products": [
			{
				"product_code": "470136",
				"description": "DISJ. PH/N SN201T-C10 U / 3KA",
				"quantity": 72,
				"net_price": 3.91,
			}
		]
	}

	importer = NetPriceImporter(client, llm_client=FakeLLMClient(llm_response))
	importer.brand = {"id": "brand-1", "name": "ABB"}
	importer.pdf_path = Path("dummy.pdf")
	importer.pdf_text = "sample extracted text"

	summary = importer.run()

	assert summary["brand_id"] == "brand-1"
	assert summary["brand_name"] == "ABB"
	assert summary["parsed_rows"] == 1
	assert summary["rows"] == 1
	assert summary["deleted"] == 0
	assert summary["created"] == 1
	assert summary["updated"] == 0
	assert summary["skipped"] == 0
	assert any(f["product_code"] == "470136" for f in client.families)
