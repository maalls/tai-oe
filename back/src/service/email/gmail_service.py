"""Service wrapper for Gmail transport operations."""

from typing import Any

from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.repository.gmail_provider_repository import GmailProviderRepository
from src.service.email.base import EmailProviderService
from src.service.email.email_auth_service import EmailAuthService
from src.service.classification.handler_service import ClassifyService


class GmailService(EmailProviderService):
    """Expose Gmail-oriented operations for transport layers."""

    def __init__(
        self,
        repository: EmailRepository | None = None,
        provider_repository: GmailProviderRepository | None = None,
        service_factory: ServiceFactory | None = None,
        auth_service: EmailAuthService | None = None,
    ):
        self.repository = repository or EmailRepository()
        self.provider_repository = provider_repository or GmailProviderRepository()
        self.service_factory = service_factory or ServiceFactory()
        self.auth_service = auth_service or EmailAuthService()

    def _verify_sender(self, **kwargs: Any) -> None:
        self.auth_service.verify_sender(
            user_id=kwargs["user_id"],
            sender_email=kwargs["sender_email"],
            sender_name=kwargs["sender_name"],
            auth_score=kwargs["auth_score"],
            is_verified=kwargs["is_verified"],
            spf_status=kwargs["spf_status"],
            dkim_status=kwargs["dkim_status"],
            dmarc_status=kwargs["dmarc_status"],
        )

    def get_status(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_gmail_status(user_id=user_id)

    def authorize(self, redirect_url: str | None = None) -> dict[str, Any]:
        return self.provider_repository.authorize_gmail(redirect_url)

    def get_oauth_url(self, redirect_url: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_gmail_oauth_url(redirect_url, user_id=user_id)

    def revoke(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.revoke_gmail(user_id=user_id)

    def get_profile(self, user_id: str | None = None) -> dict[str, Any]:
        return self.provider_repository.get_gmail_profile(user_id=user_id)

    def oauth_callback(self, code: str, state: str | None = None) -> dict[str, Any]:
        return self.provider_repository.handle_gmail_oauth_callback(code=code, state=state)

    def list_messages(self, user_id: str, max_results: int = 20, force: bool = False) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.fetch_emails(
            user_id=user_id,
            max_results=max_results,
            force=force,
            verify_sender_callback=self._verify_sender,
        )

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

    def classify_email(self, email_id: str, user_id: str, force: bool = True) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return ClassifyService(service_factory=self.service_factory, repository=self.repository).handle_classify(
            email_uuid=email_id,
            user_id=user_id,
            force=force,
        )

    def resync_email(self, email_id: str, provider_message_id: str, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        if not provider_message_id:
            return {"status": "error", "message": "Missing provider_message_id"}
        return self.repository.resync_email_from_gmail(
            email_id=email_id,
            provider_message_id=provider_message_id,
            user_id=user_id,
            verify_sender_callback=self._verify_sender,
        )

    def delete_email(self, email_id: str, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.delete_email(email_id=email_id, user_id=user_id)

    def list_attachments(self, email_id: str, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return {"status": "ok", "attachments": self.repository.list_attachments(email_id=email_id, user_id=user_id)}

    def delete_attachment(self, attachment_id: str, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        return self.repository.delete_attachment(attachment_id=attachment_id, user_id=user_id)

    def download_attachment(self, attachment_id: str, user_id: str | None):
        return self.repository.get_attachment_download(attachment_id=attachment_id, user_id=user_id)
