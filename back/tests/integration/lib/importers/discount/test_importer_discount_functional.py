import json
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.infrastructure.clients.llm import get_llm_service
from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.importers.discount import DiscountImporter


@pytest.mark.slow
@pytest.mark.timeout(60)
def test_set_brand_abb_success() -> None:
    back_root = Path(__file__).resolve().parents[4]
    env_path = back_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)

    importer = DiscountImporter(get_supabase_service(), llm_client=object())

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

    importer = DiscountImporter(get_supabase_service(), llm_client=object())

    with pytest.raises(ValueError, match="Brand not found"):
        importer.setBrand("ABC")


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


@pytest.mark.skip(reason="Fichier PDF manquant: REMISES FAMILLES 2025.pdf")
def test_parse_discounts_using_vision_matches_expected_json() -> None:
    back_root = Path(__file__).resolve().parents[4]
    env_path = back_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)

    assets_dir = Path(__file__).resolve().parents[1] / "assets"
    pdf_path = assets_dir / "REMISES FAMILLES 2025.pdf"
    json_path = assets_dir / "expected_discounts.json"

    assert pdf_path.exists(), f"Missing PDF asset: {pdf_path}"
    assert json_path.exists(), f"Missing expected JSON asset: {json_path}"

    with json_path.open("r", encoding="utf-8") as f:
        expected_rows = json.load(f)

    assert isinstance(expected_rows, list) and expected_rows, "Expected JSON fixture is empty"

    importer = DiscountImporter(supabase_client=object(), llm_client=get_llm_service())
    actual_rows = importer.parseDiscountsUsingVision(pdf_path)

    actual_by_code = {
        (row.get("family_code") or "").strip(): row
        for row in actual_rows
        if (row.get("family_code") or "").strip()
    }

    expected_codes = {(row.get("family_code") or "").strip() for row in expected_rows}
    missing_codes = sorted(code for code in expected_codes if code and code not in actual_by_code)
    assert not missing_codes, f"Missing family codes from vision output: {missing_codes}"

    for expected in expected_rows:
        family_code = (expected.get("family_code") or "").strip()
        if not family_code:
            continue

        actual = actual_by_code[family_code]

        expected_description = _normalize_text(expected.get("description"))
        actual_description = _normalize_text(actual.get("description"))
        assert actual_description == expected_description

        expected_quantity = float(expected.get("quantity") or 0)
        actual_quantity = float(actual.get("quantity") or 0)
        assert abs(actual_quantity - expected_quantity) < 0.01

        expected_discount = float(expected.get("discount") or 0)
        actual_discount = float(actual.get("discount") or 0)
        assert abs(actual_discount - expected_discount) < 0.01