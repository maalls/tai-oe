"""LLM connectivity health checks for runtime startup."""

import os

from src.infrastructure.llm_factory import LLMClientFactory


def test_llm_connection() -> bool:
    """Test LLM connectivity at startup without blocking server startup."""

    def format_llm_error(error: Exception) -> str:
        parts = [f"{error.__class__.__name__}: {error}"]
        status_code = getattr(error, "status_code", None)
        if status_code is not None:
            parts.append(f"status={status_code}")

        response = getattr(error, "response", None)
        if response is not None:
            response_text = getattr(response, "text", None)
            if response_text:
                parts.append(f"response={response_text}")

        body = getattr(error, "body", None)
        if body:
            parts.append(f"body={body}")

        return " | ".join(parts)

    try:
        print("[LLM] Testing connection to LLM service...")
        factory = LLMClientFactory()
        client = factory.create_client(timeout=5)

        # A lightweight models list call verifies transport and auth without forcing
        # a full generation request, which can time out while the model is loading.
        response = client.client.models.list()
        models = []
        if hasattr(response, "data") and response.data:
            models = [getattr(item, "id", None) for item in response.data if getattr(item, "id", None)]

        requested_model = factory.get_settings().model
        if models and requested_model not in models:
            print(f"⚠️  [LLM] API reachable, but model '{requested_model}' is not in the local model list")
        else:
            print("✅ [LLM] Connection successful")
        return True
    except Exception as error:
        print(f"⚠️  [LLM] Connection failed: {format_llm_error(error)}")
        print("     LLM may be unavailable or misconfigured")
        print(f"     Make sure your LLM service is running at {os.environ.get('LLM_URL', 'http://127.0.0.1:1234')}")
        return False
