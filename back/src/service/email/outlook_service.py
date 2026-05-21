"""Service wrapper for Outlook transport operations."""

from typing import Any

from src.repository.email_repository import EmailRepository
from src.repository.outlook_provider_repository import OutlookProviderRepository
from src.service.email.base import EmailProviderService


class OutlookService(EmailProviderService):
    """Expose Outlook-oriented operations for transport layers."""

    def __init__(
        self,
        repository: EmailRepository | None = None,
        provider_repository: OutlookProviderRepository | None = None,
    ):
        self.repository = repository or EmailRepository()
        self.provider_repository = provider_repository or OutlookProviderRepository()

    def get_status(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_outlook_status(user_id=user_id)

    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_outlook_oauth_url(redirect_url=redirect_url, user_id=user_id)

    def oauth_callback(self, code: str, state: str | None = None) -> dict[str, Any]:
        return self.provider_repository.handle_outlook_oauth_callback(code=code, state=state)

    def get_profile(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_outlook_profile(user_id=user_id)

    def revoke(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.revoke_outlook(user_id=user_id)

    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.provider_repository.list_outlook_messages(user_id=user_id, max_results=max_results)
