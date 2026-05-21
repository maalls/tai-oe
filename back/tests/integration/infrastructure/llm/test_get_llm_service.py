from pathlib import Path
import os

import pytest
from dotenv import load_dotenv

from src.infrastructure.clients.llm import get_llm_service


def _require_live_llm_tests() -> None:
	if os.getenv("RUN_LLM_TESTS", "").lower() not in {"1", "true", "yes"}:
		pytest.skip("Live LLM tests disabled. Set RUN_LLM_TESTS=1 to enable.")


@pytest.mark.slow
@pytest.mark.timeout(60)
def test_get_llm_service_and_query_json() -> None:
	_require_live_llm_tests()

	back_root = Path(__file__).resolve().parents[4]
	env_path = back_root / ".env"
	if env_path.exists():
		load_dotenv(env_path, override=False)

	try:
		llm = get_llm_service()
	except ImportError as exc:
		pytest.skip(f"LLM configuration is missing: {exc}")

	result = llm.ask_json(
		system_prompt="Return only valid JSON.",
		user_content='Return this exact JSON object: {"status":"ok","value":42}',
		temperature=0.0,
		max_tokens=128,
	)

	assert isinstance(result, dict), f"Expected dict JSON response, got: {type(result)}"
	assert result.get("status") == "ok", f"Unexpected status value: {result}"
	assert result.get("value") == 42, f"Unexpected value field: {result}"
