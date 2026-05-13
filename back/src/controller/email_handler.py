"""Email-related request handlers for Gmail operations."""

from typing import Dict
from src.infrastructure.factory import ServiceFactory


def _get_legacy_repo():
    """Create legacy email repository lazily to avoid import-time side effects."""
    from src.repository.email_repository import EmailRepository

    return EmailRepository()


class EmailHandlers:
    """Handle email-related API requests.
    
    This class acts as a controller/handler layer that delegates
    business logic to the EmailRepository.
    """
    
    def __init__(self, service_factory: ServiceFactory = None):
        """Initialize email handlers."""
        self._repository = None
        self.service_factory = service_factory or ServiceFactory()

    @property
    def repository(self):
        if self._repository is None:
            self._repository = _get_legacy_repo()
        return self._repository
    
    def handle_gmail_authorize(self, redirect_url: str = None) -> Dict:
        """Trigger Gmail OAuth2 authorization flow.
        
        Parameters
        ----------
        redirect_url : str, optional
            URL to redirect to after successful authorization
        
        Returns
        -------
        Dict
            Response with status and message
        """
        return self.repository.authorize_gmail(redirect_url)

    def get_gmail_status(self, user_id: str = None) -> Dict:
        """Get the current status of Gmail."""
        return self.repository.get_gmail_status(user_id=user_id)

    def revoke_gmail(self, user_id: str = None) -> Dict:
        """Revoke Gmail authorization."""
        return self.repository.revoke_gmail(user_id=user_id)

    def get_gmail_profile(self, user_id: str = None) -> Dict:
        """Get Gmail profile and permissions."""
        return self.repository.get_gmail_profile(user_id=user_id)

    def get_imap_status(self, user_id: str) -> Dict:
        """Get IMAP configuration status."""
        return self.repository.get_imap_status(user_id)

    def get_imap_config(self, user_id: str) -> Dict:
        """Get IMAP configuration without secret value."""
        return self.repository.get_imap_config(user_id)

    def save_imap_config(self, user_id: str, payload: Dict) -> Dict:
        """Persist IMAP configuration for a user."""
        return self.repository.save_imap_config(user_id, payload)

    def clear_imap_config(self, user_id: str) -> Dict:
        """Remove IMAP configuration for a user."""
        return self.repository.clear_imap_config(user_id)

    def test_imap_connection(self, user_id: str) -> Dict:
        """Test IMAP connectivity for a user."""
        return self.repository.test_imap_connection(user_id)

    def get_gmail_oauth_url(self, redirect_url: str = None, user_id: str = None) -> Dict:
        """Start Gmail OAuth web flow."""
        return self.repository.get_gmail_oauth_url(redirect_url, user_id=user_id)

    def handle_gmail_oauth_callback(self, code: str, state: str = None) -> Dict:
        """Handle Gmail OAuth callback."""
        return self.repository.handle_gmail_oauth_callback(code, state)
    
    def handle_gmail_list_messages(
        self,
        max_results: int = 20,
        user_id: str = None,
        save_to_db: bool = True,
        force: bool = False
    ) -> Dict:
        """List messages from Gmail inbox.
        Uses cached results from database if fetched within last 30 seconds.
        
        Parameters
        ----------
        max_results : int
            Maximum number of messages to return
        user_id : str, optional
            Supabase user ID for saving emails to database
        save_to_db : bool
            Whether to save emails to Supabase database
        force : bool
            Force fetch from Gmail API, bypassing cache
        
        Returns
        -------
        Dict
            Response with list of messages
        """
        print(f"[EmailHandlers] Listing Gmail messages for user {user_id}, max_results={max_results}, save_to_db={save_to_db}, force={force}")
        return self.repository.fetch_emails(user_id, max_results=max_results, force=force)

    def handle_classify_unclassified(
        self,
        user_id: str,
        limit: int = 200,
    ) -> Dict:
        """Classify unclassified emails using the new workflow (fail-fast)."""
        if not user_id:
            return {
                "status": "error",
                "message": "user_id is required",
            }

        try:
            workflow = self.service_factory.create_email_workflow_service()
            emails = workflow.email_service.get_all_unclassified(limit=limit, user_id=user_id)

            classified = 0
            errors = []
            for email in emails:
                try:
                    workflow.process_new_email(email.id)
                    classified += 1
                except Exception as exc:
                    errors.append({"email_id": email.id, "error": str(exc)})

            return {
                "status": "ok",
                "workflow": "new",
                "classified": classified,
                "skipped": len(errors),
                "errors": errors,
            }
        except Exception as exc:
            print(f"[EmailHandlers] New workflow failed (fail-fast mode): {exc}")
            return {
                "status": "error",
                "workflow": "new",
                "message": f"New workflow failed: {exc}",
            }
    
    def handle_send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str = None,
        cc: str = None
    ) -> Dict:
        """Send an email with optional attachment.
        
        Parameters
        ----------
        to : str
            Recipient email address
        subject : str
            Email subject
        body : str
            Email body
        attachment_path : str, optional
            Path to attachment file
        
        Returns
        -------
        Dict
            Response with status and message
        """
        return self.repository.send_email(to, subject, body, attachment_path, cc=cc)

    def handle_send_email_with_attachments(
        self,
        to: list,
        cc: list,
        bcc: list = None,
        subject: str = '',
        body: str = '',
        attachment_paths: list = None,
        user_id: str = None,
    ) -> Dict:
        """Send an email with optional attachments to multiple recipients.

        Parameters
        ----------
        to : list
            List of recipient email addresses
        cc : list
            List of CC email addresses
        subject : str
            Email subject
        body : str
            Email body
        attachment_paths : list, optional
            List of attachment file paths (uses first if provided)

        Returns
        -------
        Dict
            Response with status and message
        """
        to_emails = ", ".join([e for e in (to or []) if e])
        cc_emails = ", ".join([e for e in (cc or []) if e]) if cc else None
        bcc_emails = ", ".join([e for e in (bcc or []) if e]) if bcc else None
        attachment_path = None
        if attachment_paths:
            attachment_path = attachment_paths[0]

        return self.repository.send_email(
            to=to_emails,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            cc=cc_emails,
            bcc=bcc_emails,
            user_id=user_id,
        )
    
    def handle_get_message_body(self, uuid: str, user_id: str = None) -> Dict:
        """Get the full content of a message.
        
        Parameters
        ----------
        uuid : str
            ID of the message to fetch
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with full message content
        """
        return self.repository.get_message_body(uuid, user_id)

    def handle_email_attachment_download(self, attachment_id: str, user_id: str = None):
        """Download an email attachment.
        
        Parameters
        ----------
        attachment_id : str
            ID of the attachment to download
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Tuple of (status_code, headers, file_content)
            For serving as file download
        """
        return self.repository.get_attachment_download(attachment_id, user_id)

    def handle_email_attachment_delete(self, attachment_id: str, user_id: str = None) -> Dict:
        """Delete an email attachment.

        Parameters
        ----------
        attachment_id : str
            ID of the attachment to delete
        user_id : str, optional
            User ID for authorization
        """
        return self.repository.delete_attachment(attachment_id, user_id)

    def handle_email_delete(self, email_id: str, user_id: str = None) -> Dict:
        """Delete an email and all related records.

        Parameters
        ----------
        email_id : str
            ID of the email to delete
        user_id : str, optional
            User ID for authorization
        """
        return self.repository.delete_email(email_id, user_id)

    def handle_extract_contact_from_email(self, email_id: str = None, email_body: str = None, user_id: str = None) -> Dict:
        """Extract contact and account information from email body using LLM.
        
        Parameters
        ----------
        email_id : str, optional
            ID of the email
        email_body : str
            Email body content to extract from
        user_id : str, optional
            User ID for database operations
        
        Returns
        -------
        Dict
            Response with extracted contact and account information
        """
        return self.repository.extract_contact_from_email_body(email_id=email_id, email_body=email_body, user_id=user_id)

    def handle_get_email_auth_status(self, email_id: str, user_id: str) -> Dict:
        """Get authentication status for an email.
        
        Parameters
        ----------
        email_id : str
            ID of the email
        user_id : str
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with authentication status (SPF, DKIM, DMARC) and trust score
        """
        try:
            email = self.repository.db_handler.get_email(email_id, user_id)
            
            if not email:
                return {
                    "status": "error",
                    "message": "Email not found"
                }
            
            return {
                "status": "ok",
                "data": {
                    "email_id": email_id,
                    "from_email": email.get("from_email"),
                    "from_name": email.get("from_name"),
                    "spf_status": email.get("spf_status", "NONE"),
                    "dkim_status": email.get("dkim_status", "NONE"),
                    "dmarc_status": email.get("dmarc_status", "NONE"),
                    "auth_score": email.get("auth_score", 0),
                    "is_verified": email.get("is_verified", False),
                    "sender_verified_at": email.get("sender_verified_at")
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def handle_get_high_risk_senders(self, user_id: str) -> Dict:
        """Get list of high-risk senders (low trust score).
        
        Parameters
        ----------
        user_id : str
            User ID
        
        Returns
        -------
        Dict
            Response with list of high-risk senders
        """
        try:
            from src.controller.email.auth_handler import EmailAuthHandler
            
            auth_handler = EmailAuthHandler()
            senders = auth_handler.get_high_risk_senders(user_id, trust_score_threshold=30)
            
            return {
                "status": "ok",
                "data": senders,
                "total": len(senders)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def handle_get_verified_senders(self, user_id: str) -> Dict:
        """Get list of verified senders (SPF+DKIM+DMARC all pass).
        
        Parameters
        ----------
        user_id : str
            User ID
        
        Returns
        -------
        Dict
            Response with list of verified senders
        """
        try:
            from src.controller.email.auth_handler import EmailAuthHandler
            
            auth_handler = EmailAuthHandler()
            senders = auth_handler.get_verified_senders(user_id, limit=50)
            
            return {
                "status": "ok",
                "data": senders,
                "total": len(senders)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
