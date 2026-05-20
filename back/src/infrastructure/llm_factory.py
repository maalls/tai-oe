"""Factory helpers for constructing LLM clients from config.yml."""

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse
import yaml
from src.infrastructure.clients.llm import LLMClient

# FIXME: refactor to use src/llm get_llm_service which is configured with the back/.env environment.
DEFAULT_LLM_URL = os.environ.get("LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL", "Qwen2.5-7B-Instruct")
DEFAULT_LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _normalize_base_url(llm_url: str) -> str:
    """Normalize chat completions URL to the base /v1 endpoint."""

    normalized = llm_url.replace("/v1/chat/completions", "/v1")
    parsed = urlparse(normalized)

    path = parsed.path.rstrip("/")
    if not path or path == "":
        parsed = parsed._replace(path="/v1")
    elif not path.endswith("/v1") and not path.startswith("/v1/"):
        # Preserve any existing non-OpenAI path but make the common Ollama host-only
        # configuration OpenAI-compatible by appending /v1.
        parsed = parsed._replace(path=f"{path}/v1")

    # Legacy configs used the machine's Wi-Fi LAN IP for a local LLM server.
    # That breaks as soon as the Wi-Fi interface disappears. Route that exact
    # legacy endpoint through loopback instead so local extraction still works
    # when offline.
    if parsed.hostname == "192.168.1.5":
        hostname = "127.0.0.1"
        netloc = hostname
        if parsed.port:
            netloc = f"{hostname}:{parsed.port}"
        parsed = parsed._replace(netloc=netloc)

    return urlunparse(parsed)


class LLMSettings:
    """Lightweight settings holder for LLM configuration."""

    def __init__(self, url: str, model: str, api_key: Optional[str] = None):
        self.url = url
        self.model = model
        self.api_key = api_key

    @property
    def base_url(self) -> str:
        return _normalize_base_url(self.url)


class LLMClientFactory:
    """Load LLM configuration and build clients with consistent defaults."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

    def _find_config(self) -> str:
        """Find config.yml in standard locations."""

        current_dir = Path(__file__).parent.parent
        candidates = [
            current_dir / "config.yml",
            Path.cwd() / "config.yml",
            Path.cwd() / "back" / "config.yml",
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        # If not found, return a default path to allow env-only configuration
        return str(current_dir / "config.yml")

    def _load_config(self) -> dict:
        if not os.path.exists(self.config_path):
            return {}

        with open(self.config_path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def get_settings(self, llm_url: Optional[str] = None, model: Optional[str] = None) -> LLMSettings:
        cfg_llm = self.config.get("llm", {}) if isinstance(self.config, dict) else {}

        env_url = os.environ.get("LLM_URL")
        env_model = os.environ.get("LLM_MODEL")
        env_api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")

        url = llm_url or env_url or cfg_llm.get("url") or DEFAULT_LLM_URL
        mdl = model or env_model or cfg_llm.get("model") or DEFAULT_LLM_MODEL
        key = env_api_key or cfg_llm.get("api_key") or DEFAULT_LLM_API_KEY

        if isinstance(key, str) and not key.strip():
            key = None

        return LLMSettings(url=url, model=mdl, api_key=key)

    def create_client(
        self,
        llm_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = 60,
        client_cls=None,
    ):
        settings = self.get_settings(llm_url=llm_url, model=model)
        klass = client_cls or LLMClient
        if klass is None:  # pragma: no cover - requires real dependency
            raise ImportError("LLMClient dependency is missing; ensure back/script is on sys.path")

        resolved_api_key = api_key if api_key is not None else settings.api_key
        return klass(
            base_url=settings.base_url,
            model=settings.model,
            api_key=resolved_api_key,
            timeout=timeout,
        )

