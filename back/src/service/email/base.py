"""Shared interface for OAuth email providers."""

from abc import ABC, abstractmethod
from typing import Any


class EmailProviderService(ABC):
    @abstractmethod
    def get_status(self, user_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def oauth_callback(self, code: str, state: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_profile(self, user_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def revoke(self, user_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict[str, Any]:
        raise NotImplementedError
