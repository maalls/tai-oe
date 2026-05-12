import os
import sys
import json
from pathlib import Path

import pytest
from dotenv import load_dotenv

# File location: back/tests/integration/text/reader/test_extract_rfp_from_pdf_llm.py
# back/ is parents[4]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.pdf.extract_text import extract_text
from src.text.reader import extract_rfp_from_text


def _flatten_products(payload):
    """Accept both canonical {'products': [...]} and nested dict formats."""
    if not isinstance(payload, dict):
        return []

    products = payload.get("products")
    if isinstance(products, list):
        return [p for p in products if isinstance(p, dict)]

    flattened = []
    for maybe_brand_map in payload.values():
        if not isinstance(maybe_brand_map, dict):
            continue
        for maybe_product in maybe_brand_map.values():
            if not isinstance(maybe_product, dict):
                continue
            if any(
                maybe_product.get(k) is not None
                for k in ("part_number", "sku", "reference", "quantity", "description")
            ):
                flattened.append(maybe_product)
    return flattened


def _norm_text(value):
    return str(value or "").strip().lower()


def _norm_qty(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return s


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.timeout(180)
def test_llm_extracts_products_reference_quantity_from_rfp_pdf():
    """Real integration test: PDF -> text -> LLM extraction (no mocks)."""

    pdf_path = PROJECT_ROOT / "tests" / "assets" / "rfp" / "rfp.pdf"
    assert pdf_path.exists(), f"Missing PDF fixture: {pdf_path}"

    raw_text = extract_text(pdf_path)
    assert raw_text and raw_text.strip(), "No text extracted from PDF"

    # Ensure cold-start-safe timeout for local Ollama model loading.
    os.environ["LLM_TIMEOUT"] = "240"

    rfp_data = extract_rfp_from_text(raw_text)
    assert isinstance(rfp_data, dict), f"Expected dict from LLM, got {type(rfp_data)}"

    products = _flatten_products(rfp_data)
    assert products, "LLM did not extract any products from the PDF"

    # Strict schema for this test: quantity, manufacturer, part_number.
    strict_products = []
    for p in products:
        if not isinstance(p, dict):
            continue
        part_number = p.get("part_number") or p.get("sku") or p.get("reference")
        strict_products.append(
            {
                "quantity": p.get("quantity"),
                "manufacturer": p.get("manufacturer") or p.get("brand"),
                "part_number": part_number,
            }
        )

    assert strict_products, "No normalized products found"

    for idx, sp in enumerate(strict_products):
        assert "quantity" in sp, f"Product #{idx} missing quantity key"
        assert "manufacturer" in sp, f"Product #{idx} missing manufacturer key"
        assert "part_number" in sp, f"Product #{idx} missing part_number key"

    fully_populated = [
        sp for sp in strict_products
        if _norm_qty(sp.get("quantity")) is not None
        and _norm_text(sp.get("manufacturer"))
        and _norm_text(sp.get("part_number"))
    ]
    assert len(fully_populated) >= 3, (
        "Expected at least 3 products with strict fields populated "
        "(quantity + manufacturer + part_number)"
    )

    expected_path = (
        PROJECT_ROOT
        / "tests"
        / "integration"
        / "assets"
        / "text"
        / "reader"
        / "expected_rfp_extract_rfp_pdf.json"
    )
    assert expected_path.exists(), f"Missing expected fixture: {expected_path}"
    expected_payload = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_products = _flatten_products(expected_payload.get("result") or {})

    expected_keys = {
        (_norm_text(p.get("manufacturer")), _norm_text(p.get("part_number") or p.get("sku") or p.get("reference")))
        for p in expected_products
        if _norm_text(p.get("manufacturer")) and _norm_text(p.get("part_number") or p.get("sku") or p.get("reference"))
    }
    extracted_keys = {
        (_norm_text(p.get("manufacturer")), _norm_text(p.get("part_number")))
        for p in fully_populated
    }
    overlap = expected_keys & extracted_keys
    assert len(overlap) >= 3, (
        "LLM extraction drift is too high vs expected strict fields "
        f"(overlap={len(overlap)})"
    )
