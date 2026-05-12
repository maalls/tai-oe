import json
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.llm import get_llm_service
from src.net_price.importer import NetPriceImporter
from src.supabase import get_supabase_service


@pytest.mark.slow
@pytest.mark.timeout(60)
def test_set_brand_abb_success() -> None:
	back_root = Path(__file__).resolve().parents[4]
	env_path = back_root / ".env"
	if env_path.exists():
		load_dotenv(env_path, override=False)

	importer = NetPriceImporter(get_supabase_service(), llm_client=object())

	brand = importer.setBrand("ABB")

	assert isinstance(brand, dict)
	assert brand.get("id")
	assert brand.get("name") == "ABB"


@pytest.mark.slow
@pytest.mark.timeout(60)
def test_set_brand_abc_fail() -> None:
	back_root = Path(__file__).resolve().parents[4]
	env_path = back_root / ".env"
	if env_path.exists():
		load_dotenv(env_path, override=False)

	importer = NetPriceImporter(get_supabase_service(), llm_client=object())

	with pytest.raises(ValueError, match="Brand not found"):
		importer.setBrand("ABC")


def _normalize_text(value: str) -> str:
	return " ".join((value or "").strip().split())


@pytest.mark.slow
@pytest.mark.timeout(180)
def test_parse_net_prices_matches_expected_json() -> None:
	back_root = Path(__file__).resolve().parents[4]
	env_path = back_root / ".env"
	if env_path.exists():
		load_dotenv(env_path, override=False)

	assets_dir = Path(__file__).resolve().parents[1] / "assets"
	pdf_path = assets_dir / "test_asset_abb_2026.pdf"
	json_path = assets_dir / "net_prices_expected.json"

	assert pdf_path.exists(), f"Missing PDF asset: {pdf_path}"
	assert json_path.exists(), f"Missing expected JSON asset: {json_path}"

	with json_path.open("r", encoding="utf-8") as f:
		expected_json = json.load(f)

	expected_rows = expected_json.get("products") if isinstance(expected_json, dict) else None

	assert isinstance(expected_rows, list) and expected_rows, "Expected JSON fixture is empty"

	importer = NetPriceImporter(supabase_client=object(), llm_client=get_llm_service())
	importer.load_pdf(pdf_path)
	actual_rows = importer.parseNetPrices()

	actual_by_code = {
		(row.get("product_code") or "").strip(): row
		for row in actual_rows
		if (row.get("product_code") or "").strip()
	}

	expected_codes = {(row.get("product_code") or "").strip() for row in expected_rows}
	missing_codes = sorted(code for code in expected_codes if code and code not in actual_by_code)
	assert not missing_codes, f"Missing product codes from LLM output: {missing_codes}"

	for expected in expected_rows:
		product_code = (expected.get("product_code") or "").strip()
		if not product_code:
			continue

		actual = actual_by_code[product_code]

		expected_local_code = (expected.get("local_code") or "").strip()
		assert (actual.get("local_code") or "").strip() == expected_local_code

		expected_description = _normalize_text(expected.get("description") or "")
		actual_description = _normalize_text(actual.get("description") or "")
		assert actual_description == expected_description

		expected_quantity = float(expected.get("quantity") or 0)
		actual_quantity = float(actual.get("quantity") or 0)
		assert abs(actual_quantity - expected_quantity) < 0.01

		expected_net_price = float(expected.get("net_price") or 0)
		actual_net_price = float(actual.get("net_price") or 0)
		assert abs(actual_net_price - expected_net_price) < 0.01
