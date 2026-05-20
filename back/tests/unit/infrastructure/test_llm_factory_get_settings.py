from src.infrastructure.llm_factory import LLMClientFactory


class _FakeLLMClient:
    def __init__(self, base_url, model, api_key=None, timeout=None):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = timeout


def test_get_settings_reads_llm_api_key_from_env(monkeypatch, tmp_path):
    config_path = tmp_path / "missing.yml"
    monkeypatch.setenv("LLM_URL", "https://api.openai.com")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "sk-llm-env")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    factory = LLMClientFactory(config_path=str(config_path))
    settings = factory.get_settings()

    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.model == "gpt-4o-mini"
    assert settings.api_key == "sk-llm-env"


def test_get_settings_falls_back_to_openai_api_key(monkeypatch, tmp_path):
    config_path = tmp_path / "missing.yml"
    monkeypatch.setenv("LLM_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("LLM_MODEL", "gpt-4.1-mini")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-env")

    factory = LLMClientFactory(config_path=str(config_path))
    settings = factory.get_settings()

    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.api_key == "sk-openai-env"


def test_create_client_passes_api_key_from_settings(monkeypatch, tmp_path):
    config_path = tmp_path / "missing.yml"
    monkeypatch.setenv("LLM_URL", "https://api.openai.com")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("LLM_API_KEY", "sk-client-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    factory = LLMClientFactory(config_path=str(config_path))
    client = factory.create_client(client_cls=_FakeLLMClient, timeout=7)

    assert client.base_url == "https://api.openai.com/v1"
    assert client.model == "gpt-4o"
    assert client.api_key == "sk-client-key"
    assert client.timeout == 7