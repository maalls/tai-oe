"""Service wrapper for Gmail transport operations."""

from typing import Any

from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository


class GmailService:
    """Expose Gmail-oriented operations for transport layers."""

    def __init__(self, repository: EmailRepository | None = None, service_factory: ServiceFactory | None = None):
        self.repository = repository or EmailRepository()
        self.service_factory = service_factory or ServiceFactory()

    def get_status(self, user_id: str | None = None) -> dict[str, Any]:
        return self.repository.get_gmail_status(user_id=user_id)

    def authorize(self, redirect_url: str | None = None) -> dict[str, Any]:
        return self.repository.authorize_gmail(redirect_url)

    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        return self.repository.get_gmail_oauth_url(redirect_url, user_id=user_id)

    def revoke(self, user_id: str | None = None) -> dict[str, Any]:
        return self.repository.revoke_gmail(user_id=user_id)

    def get_profile(self, user_id: str | None = None) -> dict[str, Any]:
        return self.repository.get_gmail_profile(user_id=user_id)

    def oauth_callback(self, code: str, state: str | None = None) -> dict[str, Any]:
        return self.repository.handle_gmail_oauth_callback(code=code, state=state)

    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.fetch_emails(user_id=user_id, max_results=max_results, force=force)

    def classify_unclassified(self, user_id: str, limit: int = 200) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        try:
            workflow = self.service_factory.create_email_workflow_service()
            return workflow.classify_unclassified(user_id=user_id, limit=limit)
        except Exception as exc:
            return {
                "status": "error",
                "workflow": "new",
                "message": f"New workflow failed: {exc}",
            }

    def get_message_body(self, message_id: str, user_id: str | None) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.get_message_body(uuid=message_id, user_id=user_id)

    def get_imap_status(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.get_imap_status(user_id=user_id)

    def get_imap_config(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.get_imap_config(user_id=user_id)

    def save_imap_config(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.save_imap_config(user_id=user_id, payload=payload)

    def test_imap_connection(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.test_imap_connection(user_id=user_id)

    def clear_imap_config(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.clear_imap_config(user_id=user_id)
