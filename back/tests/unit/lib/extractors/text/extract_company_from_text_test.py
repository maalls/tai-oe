from pathlib import Path
import os
import pytest

from src.lib.extractors.text_reader import extract_company_from_text


def _require_live_llm_tests() -> None:
	if os.getenv("RUN_LLM_TESTS", "").lower() not in {"1", "true", "yes"}:
		pytest.skip("Live LLM tests disabled. Set RUN_LLM_TESTS=1 to enable.")

@pytest.mark.slow
@pytest.mark.timeout(180)

def test_extract_company_from_text():
	_require_live_llm_tests()

	sample_path = Path(__file__).parent / "sample" / "rfp.txt"
	assert sample_path.exists(), f"Sample text not found: {sample_path}"
	content = sample_path.read_text(encoding="utf-8").strip()
	assert content, "Sample text is empty"

	result = extract_company_from_text(content)
	assert isinstance(result, dict), "Expected JSON object from LLM"
	print("Extracted company data:", result)
	print("company name:", result.get("company_name", "N/A"))
	assert result.get("company_name") == "S.A.R.L. CABLOMAN", f"Expected company_name 'S.A.R.L. CABLOMAN', got '{result.get('company_name')}'"