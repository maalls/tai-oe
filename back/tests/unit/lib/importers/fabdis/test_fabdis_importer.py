from pathlib import Path

import pandas as pd

from src.lib.importers.fabdis import FabdisImporter


class FakePandas:
	def __init__(self, workbook: object):
		self.workbook = workbook
		self.called_with = None
		self.read_excel_called_with = None
		self.cartouche_df = pd.DataFrame()
		self.commerce_df = pd.DataFrame(
			columns=[
				"MARQUE",
				"REFCIALE",
				"LIBELLE40",
				"LIBELLE80",
				"LIBELLE240",
				"TARIF",
				"TVA",
				"FAM1",
				"FAM1L",
				"FAM2",
				"FAM2L",
				"FAM3",
				"FAM3L",
			]
		)

	def ExcelFile(self, fabdis_file: Path) -> object:
		self.called_with = fabdis_file
		return self.workbook

	def read_excel(self, workbook: object, sheet_name: str, **kwargs):
		self.read_excel_called_with = (workbook, sheet_name, kwargs)
		if sheet_name == "B00_CARTOUCHE":
			return self.cartouche_df
		if sheet_name == "B01_COMMERCE":
			return self.commerce_df
		raise AssertionError(f"Unexpected sheet: {sheet_name}")

	def isna(self, value: object) -> bool:
		return pd.isna(value)


class FakeResponse:
	def __init__(self, data, error=None):
		self.data = data
		self.error = error


class FakeQuery:
	def __init__(self, client, table_name: str):
		self.client = client
		self.table_name = table_name
		self.filters = []
		self.payload = None

	def select(self, fields: str):
		return self

	def eq(self, column: str, value: object):
		self.filters.append((column, value))
		return self

	def is_(self, column: str, value: object):
		self.filters.append((f"{column}__is", value))
		return self

	def limit(self, value: int):
		return self

	def insert(self, payload: dict[str, object]):
		self.payload = payload
		return self

	def execute(self):
		return self.client.execute(self)


class FakeSupabaseClient:
	def __init__(self):
		self.vendor_rows = {"ABB": "vendor-1"}
		self.brand_rows = {("vendor-1", "ABB"): "brand-1"}
		self.product_rows = {("brand-1", "ABB-SKU"): "product-1"}
		self.family_rows = {("brand-1", None, "R"): "family-1"}
		self.product_family_rows = {("product-1", "family-1")}
		self.inserted_vendors = []
		self.inserted_brands = []
		self.inserted_products = []
		self.inserted_families = []
		self.inserted_product_families = []

	def table(self, table_name: str):
		return FakeQuery(self, table_name)

	def execute(self, query: FakeQuery):
		if query.table_name == "vendor" and query.payload is None:
			vendor_name = dict(query.filters).get("name")
			vendor_id = self.vendor_rows.get(vendor_name)
			if vendor_id is None:
				return FakeResponse([])
			return FakeResponse([{"id": vendor_id}])

		if query.table_name == "vendor" and query.payload is not None:
			vendor_id = f"vendor-{len(self.vendor_rows) + 1}"
			self.vendor_rows[query.payload["name"]] = vendor_id
			self.inserted_vendors.append(query.payload)
			return FakeResponse([{"id": vendor_id}])

		if query.table_name == "brand" and query.payload is None:
			filters = dict(query.filters)
			if "vendor_id" in filters and "name" in filters:
				brand_id = self.brand_rows.get((filters.get("vendor_id"), filters.get("name")))
				if brand_id is None:
					return FakeResponse([])
				return FakeResponse([{"id": brand_id}])

			if "name" in filters and "vendor_id" not in filters:
				matches = [
					{"id": brand_id}
					for (vendor_id, brand_name), brand_id in self.brand_rows.items()
					if brand_name == filters.get("name")
				]
				return FakeResponse(matches)

			raise AssertionError(f"Unsupported brand filters: {filters}")

		if query.table_name == "brand" and query.payload is not None:
			brand_id = f"brand-{len(self.brand_rows) + 1}"
			key = (query.payload["vendor_id"], query.payload["name"])
			self.brand_rows[key] = brand_id
			self.inserted_brands.append(query.payload)
			return FakeResponse([{"id": brand_id}])

		if query.table_name == "product" and query.payload is None:
			filters = dict(query.filters)
			product_id = self.product_rows.get((filters.get("brand_id"), filters.get("sku")))
			if product_id is None:
				return FakeResponse([])
			return FakeResponse([{"id": product_id}])

		if query.table_name == "product" and query.payload is not None:
			product_id = f"product-{len(self.product_rows) + 1}"
			key = (query.payload["brand_id"], query.payload["sku"])
			self.product_rows[key] = product_id
			self.inserted_products.append(query.payload)
			return FakeResponse([{"id": product_id}])

		if query.table_name == "family" and query.payload is None:
			filters = dict(query.filters)
			family_id = self.family_rows.get(
				(filters.get("brand_id"), filters.get("type"), filters.get("code"))
			)
			if family_id is None:
				return FakeResponse([])
			return FakeResponse([{"id": family_id}])

		if query.table_name == "family" and query.payload is not None:
			family_id = f"family-{len(self.family_rows) + 1}"
			key = (query.payload["brand_id"], query.payload["type"], query.payload["code"])
			self.family_rows[key] = family_id
			self.inserted_families.append(query.payload)
			return FakeResponse([{"id": family_id}])

		if query.table_name == "product_family" and query.payload is None:
			filters = dict(query.filters)
			key = (filters.get("product_id"), filters.get("family_id"))
			if key in self.product_family_rows:
				return FakeResponse([{"product_id": key[0]}])
			return FakeResponse([])

		if query.table_name == "product_family" and query.payload is not None:
			key = (query.payload["product_id"], query.payload["family_id"])
			self.product_family_rows.add(key)
			self.inserted_product_families.append(query.payload)
			return FakeResponse([query.payload])

		raise AssertionError(f"Unexpected query: {query.table_name}")


def test_load_assigns_workbook(tmp_path: Path):
	fabdis_file = tmp_path / "fabdis.xlsx"
	fabdis_file.write_text("placeholder", encoding="utf-8")

	workbook = object()
	fake_pandas = FakePandas(workbook)
	importer = FabdisImporter(fake_pandas, None)

	importer.load(fabdis_file)

	assert fake_pandas.called_with == fabdis_file
	assert importer.workbook is workbook


def test_load_cartouche_returns_deduplicated_vendor_brand_rows():
	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.cartouche_df = pd.DataFrame(
		[
			{
				"FABRICANT": "ABB",
				"CARMARQUE": "ABB",
				"CARMARQUEURLT": "https://abb.example",
				"CAREMAIL": "contact@abb.example",
			},
			{
				"FABRICANT": " ABB ",
				"CARMARQUE": "ABB",
				"CARMARQUEURLT": "https://abb.example",
				"CAREMAIL": "contact@abb.example",
			},
			{
				"FABRICANT": "ABB",
				"CARMARQUE": "Hélita",
				"CARMARQUEURLT": None,
				"CAREMAIL": None,
			},
		]
	)
	importer = FabdisImporter(fake_pandas, None)
	importer.workbook = workbook

	rows = importer.load_cartouche()

	assert fake_pandas.read_excel_called_with == (
		workbook,
		"B00_CARTOUCHE",
		{"usecols": ["FABRICANT", "CARMARQUE", "CARMARQUEURLT", "CAREMAIL"]},
	)
	assert rows == [
		{
			"vendor_name": "ABB",
			"brand_name": "ABB",
			"brand_website": "https://abb.example",
			"brand_email": "contact@abb.example",
		},
		{
			"vendor_name": "ABB",
			"brand_name": "Hélita",
			"brand_website": None,
			"brand_email": None,
		},
	]
	assert importer.cartouche_rows == rows


def test_load_cartouche_fails_when_vendor_is_missing():
	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.cartouche_df = pd.DataFrame(
		[
			{
				"FABRICANT": None,
				"CARMARQUE": "ABB",
				"CARMARQUEURLT": None,
				"CAREMAIL": None,
			}
		]
	)
	importer = FabdisImporter(fake_pandas, None)
	importer.workbook = workbook

	try:
		importer.load_cartouche()
		assert False, "Expected ValueError"
	except ValueError as exc:
		assert str(exc) == "B00_CARTOUCHE row 2: FABRICANT is required"


def test_load_cartouche_fails_when_brand_is_missing():
	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.cartouche_df = pd.DataFrame(
		[
			{
				"FABRICANT": "ABB",
				"CARMARQUE": None,
				"CARMARQUEURLT": None,
				"CAREMAIL": None,
			}
		]
	)
	importer = FabdisImporter(fake_pandas, None)
	importer.workbook = workbook

	try:
		importer.load_cartouche()
		assert False, "Expected ValueError"
	except ValueError as exc:
		assert str(exc) == "B00_CARTOUCHE row 2: CARMARQUE is required"


def test_import_cartouche_inserts_only_missing_vendor_and_brand():
	supabase_client = FakeSupabaseClient()
	importer = FabdisImporter(pd, supabase_client)
	importer.cartouche_rows = [
		{
			"vendor_name": "ABB",
			"brand_name": "ABB",
			"brand_website": "https://abb.example",
			"brand_email": "contact@abb.example",
		},
		{
			"vendor_name": "ABB",
			"brand_name": "Hélita",
			"brand_website": None,
			"brand_email": None,
		},
		{
			"vendor_name": "Legrand",
			"brand_name": "Legrand",
			"brand_website": "https://legrand.example",
			"brand_email": "contact@legrand.example",
		},
	]

	rows = importer.import_cartouche()

	assert rows == [
		{
			"vendor_name": "ABB",
			"brand_name": "ABB",
			"brand_website": "https://abb.example",
			"brand_email": "contact@abb.example",
			"vendor_id": "vendor-1",
			"brand_id": "brand-1",
		},
		{
			"vendor_name": "ABB",
			"brand_name": "Hélita",
			"brand_website": None,
			"brand_email": None,
			"vendor_id": "vendor-1",
			"brand_id": "brand-2",
		},
		{
			"vendor_name": "Legrand",
			"brand_name": "Legrand",
			"brand_website": "https://legrand.example",
			"brand_email": "contact@legrand.example",
			"vendor_id": "vendor-2",
			"brand_id": "brand-3",
		},
	]
	assert supabase_client.inserted_vendors == [{"name": "Legrand"}]
	assert supabase_client.inserted_brands == [
		{
			"name": "Hélita",
			"marque": "Hélita",
			"vendor_id": "vendor-1",
			"website": None,
			"email": None,
		},
		{
			"name": "Legrand",
			"marque": "Legrand",
			"vendor_id": "vendor-2",
			"website": "https://legrand.example",
			"email": "contact@legrand.example",
		},
	]
	assert importer.last_summary == {
		"cartouche_rows": 3,
		"vendors_in_file": 2,
		"brands_in_file": 3,
		"vendors_created": 1,
		"brands_created": 2,
		"vendors_existing": 1,
		"brands_existing": 1,
	}


def test_import_runs_cartouche_flow():
	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.cartouche_df = pd.DataFrame(
		[
			{
				"FABRICANT": "ABB",
				"CARMARQUE": "ABB",
				"CARMARQUEURLT": "https://abb.example",
				"CAREMAIL": "contact@abb.example",
			}
		]
	)
	supabase_client = FakeSupabaseClient()
	importer = FabdisImporter(fake_pandas, supabase_client)
	importer.workbook = workbook

	rows = importer.run()

	assert rows == [
		{
			"vendor_name": "ABB",
			"brand_name": "ABB",
			"brand_website": "https://abb.example",
			"brand_email": "contact@abb.example",
			"vendor_id": "vendor-1",
			"brand_id": "brand-1",
		}
	]
	assert importer.imported_cartouche_rows == rows
	assert importer.last_summary == {
		"cartouche_rows": 1,
		"vendors_in_file": 1,
		"brands_in_file": 1,
		"vendors_created": 0,
		"brands_created": 0,
		"vendors_existing": 1,
		"brands_existing": 1,
		"products_in_file": 0,
		"products_created": 0,
		"products_existing": 0,
		"families_created": 0,
		"product_family_created": 0,
	}


def test_import_products_creates_product_and_families_from_commerce_rows():
	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.commerce_df = pd.DataFrame(
		[
			{
				"MARQUE": "ABB",
				"REFCIALE": "ABB-SKU",
				"LIBELLE40": "Existing Product",
				"LIBELLE80": None,
				"LIBELLE240": None,
				"TARIF": 10.5,
				"TVA": 20,
				"FAM1": "R",
				"FAM1L": "Raccordement",
				"FAM2": None,
				"FAM2L": None,
				"FAM3": None,
				"FAM3L": None,
			},
			{
				"MARQUE": "ABB",
				"REFCIALE": "ABB-SKU-NEW",
				"LIBELLE40": None,
				"LIBELLE80": "New Product",
				"LIBELLE240": None,
				"TARIF": 22.0,
				"TVA": 20,
				"FAM1": "R",
				"FAM1L": "Raccordement",
				"FAM2": "R15",
				"FAM2L": "Connexion",
				"FAM3": None,
				"FAM3L": None,
			},
		]
	)
	supabase_client = FakeSupabaseClient()
	importer = FabdisImporter(fake_pandas, supabase_client)
	importer.workbook = workbook

	rows = importer.import_products()

	assert len(rows) == 2
	assert rows[0]["product_id"] == "product-1"
	assert rows[1]["product_id"] == "product-2"
	assert supabase_client.inserted_products == [
		{
			"brand_id": "brand-1",
			"sku": "ABB-SKU-NEW",
			"name": "New Product",
			"price": 22.0,
			"default_tax_rate": 20.0,
		}
	]
	assert supabase_client.inserted_families == [
		{
			"brand_id": "brand-1",
			"type": None,
			"code": "R15",
			"name": "Connexion",
		}
	]
	assert supabase_client.inserted_product_families == [
		{"product_id": "product-2", "family_id": "family-1"},
		{"product_id": "product-2", "family_id": "family-2"},
	]
	assert importer.last_summary == {
		"products_in_file": 2,
		"products_created": 1,
		"products_existing": 1,
		"families_created": 1,
		"product_family_created": 2,
	}


def test_import_products_reuses_existing_null_type_family_with_is_null_filter():
	class _StrictNullFamilyClient(FakeSupabaseClient):
		def execute(self, query: FakeQuery):
			if query.table_name == "family" and query.payload is None:
				filters = dict(query.filters)
				brand_id = filters.get("brand_id")
				code = filters.get("code")
				if "type__is" in filters and str(filters.get("type__is")).lower() == "null":
					family_id = self.family_rows.get((brand_id, None, code))
					if family_id is None:
						return FakeResponse([])
					return FakeResponse([{"id": family_id}])

				# Simulate PostgREST behavior: eq(type, None) does not match SQL NULL rows.
				if "type" in filters and filters.get("type") is None:
					return FakeResponse([])

			return super().execute(query)

	workbook = object()
	fake_pandas = FakePandas(workbook)
	fake_pandas.commerce_df = pd.DataFrame(
		[
			{
				"MARQUE": "ABB",
				"REFCIALE": "ABB-SKU",
				"LIBELLE40": "Existing Product",
				"LIBELLE80": None,
				"LIBELLE240": None,
				"TARIF": 10.5,
				"TVA": 20,
				"FAM1": "R",
				"FAM1L": "Raccordement",
				"FAM2": None,
				"FAM2L": None,
				"FAM3": None,
				"FAM3L": None,
			}
		]
	)

	supabase_client = _StrictNullFamilyClient()
	importer = FabdisImporter(fake_pandas, supabase_client)
	importer.workbook = workbook

	rows = importer.import_products()

	assert len(rows) == 1
	assert rows[0]["product_id"] == "product-1"
	assert rows[0]["family_ids"] == ["family-1"]
	assert supabase_client.inserted_families == []
	assert importer.last_summary["families_created"] == 0
