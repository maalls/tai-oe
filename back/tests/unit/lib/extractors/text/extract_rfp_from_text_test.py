import os
from pathlib import Path

import httpx
import pytest

from src.llm import extract_json_from_text
from src.text.reader import extract_rfp_from_text
from src.infrastructure.llm_factory import DEFAULT_LLM_URL


def _llm_available() -> tuple[bool, str]:
	llm_url = os.getenv("LLM_URL", DEFAULT_LLM_URL)
	target = llm_url
	if "/v1" in llm_url:
		target = llm_url.split("/v1", 1)[0] + "/v1/models"
	try:
		resp = httpx.get(target, timeout=3)
		return resp.status_code < 500, f"{target} responded {resp.status_code}"
	except Exception as exc:
		return False, f"{target} error: {exc}"


@pytest.mark.slow
@pytest.mark.timeout(180)
def test_extract_rfp_from_text_counts_products():
	if os.getenv("RUN_LLM_LIVE") != "1":
		pytest.fail("Set RUN_LLM_LIVE=1 to run live LLM extraction test")

	reachable, detail = _llm_available()
	if not reachable:
		pytest.fail(f"LLM endpoint not reachable: {detail}")

	sample_path = Path(__file__).parent / "sample" / "rfp.txt"
	assert sample_path.exists(), f"Sample text not found: {sample_path}"
	content = sample_path.read_text(encoding="utf-8").strip()
	assert content, "Sample text is empty"

	result = extract_rfp_from_text(content)

	if isinstance(result, str):
		parsed = extract_json_from_text(result)
		assert parsed is not None, "LLM returned non-JSON content"
		result = parsed

	assert isinstance(result, dict), "Expected JSON object from LLM"
	assert "products" in result and isinstance(result["products"], list), "Missing products list"
	assert len(result["products"]) == 21, f"Expected 21 products, got {len(result['products'])}"

@pytest.mark.slow
@pytest.mark.timeout(300)
def test_extract_rfp_from_text_large_products():
	if os.getenv("RUN_LLM_LIVE") != "1":
		pytest.fail("Set RUN_LLM_LIVE=1 to run live LLM extraction test")

	reachable, detail = _llm_available()
	if not reachable:
		pytest.fail(f"LLM endpoint not reachable: {detail}")

	sample_path = Path(__file__).parent / "sample" / "rfp_large.txt"
	assert sample_path.exists(), f"Sample text not found: {sample_path}"
	content = sample_path.read_text(encoding="utf-8").strip()
	assert content, "Sample text is empty"

	result = extract_rfp_from_text(content)

	if isinstance(result, str):
		parsed = extract_json_from_text(result)
		assert parsed is not None, "LLM returned non-JSON content"
		result = parsed

	assert isinstance(result, dict), "Expected JSON object from LLM"
	assert "products" in result and isinstance(result["products"], list), "Missing products list"
	assert len(result["products"]) == 23, f"Expected 23 products, got {len(result['products'])}"