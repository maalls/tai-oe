"""Service for email authentication status and sender trust endpoints."""

from typing import Dict

from src.service.email.email_auth_service import EmailAuthService


class AuthStatusService:
    """Compose email repository and auth handler across domains."""

    def __init__(self, repository, email_auth_handler: EmailAuthService = None):
        self.repository = repository
        self.email_auth_handler = email_auth_handler or EmailAuthService()

    def get_email_auth_status(self, email_id: str, user_id: str) -> Dict:
        try:
            email = self.repository.db_handler.get_email(email_id, user_id)

            if not email:
                return {
                    "status": "error",
                    "message": "Email not found",
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
                    "sender_verified_at": email.get("sender_verified_at"),
                },
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def get_high_risk_senders(self, user_id: str) -> Dict:
        try:
            senders = self.email_auth_handler.get_high_risk_senders(user_id, trust_score_threshold=30)
            return {
                "status": "ok",
                "data": senders,
                "total": len(senders),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }

    def get_verified_senders(self, user_id: str) -> Dict:
        try:
            senders = self.email_auth_handler.get_verified_senders(user_id, limit=50)
            return {
                "status": "ok",
                "data": senders,
                "total": len(senders),
            }
        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
            }
