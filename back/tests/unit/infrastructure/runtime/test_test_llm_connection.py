from types import SimpleNamespace

from src.infrastructure.runtime import llm_health


class _OkFactory:
    def create_client(self, timeout=5):
        _ = timeout
        return SimpleNamespace(
            client=SimpleNamespace(
                models=SimpleNamespace(
                    list=lambda: SimpleNamespace(data=[SimpleNamespace(id="gpt-local")])
                )
            )
        )

    def get_settings(self):
        return SimpleNamespace(model="gpt-local")


class _FailFactory:
    def create_client(self, timeout=5):
        _ = timeout
        raise RuntimeError("boom")

    def get_settings(self):
        return SimpleNamespace(model="gpt-local")


def test_test_llm_connection_returns_true_when_models_are_listed(monkeypatch):
    monkeypatch.setattr(llm_health, "LLMClientFactory", _OkFactory)

    assert llm_health.test_llm_connection() is True


def test_test_llm_connection_returns_false_on_factory_error(monkeypatch):
    monkeypatch.setattr(llm_health, "LLMClientFactory", _FailFactory)

    assert llm_health.test_llm_connection() is False
