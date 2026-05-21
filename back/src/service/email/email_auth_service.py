"""Email authentication verification service."""

from datetime import datetime
from typing import Dict, List

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.email.auth_parser import EmailAuthParser


class EmailAuthService:
    """Handle email authentication verification and trust scoring."""

    def __init__(self):
        self.supabase = get_supabase_service()

    def _execute_raw_sql(self, query: str, params: tuple = None) -> bool:
        _ = params
        try:
            self.supabase.rpc("exec_sql", {"query": query}).execute()
            return True
        except Exception as exc:
            print(f"[EmailAuthService] Warning: Raw SQL execution not available: {exc}")
            return False

    def verify_sender(
        self,
        user_id: str,
        sender_email: str,
        sender_name: str,
        auth_score: int,
        is_verified: bool,
        spf_status: str,
        dkim_status: str,
        dmarc_status: str,
    ) -> Dict:
        try:
            sender_domain = sender_email.split("@")[1] if "@" in sender_email else ""
            response = self.supabase.table("sender_verification").select("*").eq("user_id", user_id).eq("sender_email", sender_email).execute()
            existing = response.data[0] if response.data else None

            if existing:
                auth_history = existing.get("auth_history", []) or []
                auth_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "spf": spf_status,
                    "dkim": dkim_status,
                    "dmarc": dmarc_status,
                    "score": auth_score,
                })
                if len(auth_history) > 100:
                    auth_history = auth_history[-100:]

                total_emails = existing.get("total_emails_received", 0) + 1
                verified_emails = existing.get("verified_emails_count", 0) + (1 if is_verified else 0)
                recent_scores = [h["score"] for h in auth_history[-10:]]
                new_trust_score = sum(recent_scores) // len(recent_scores)

                update_data = {
                    "trust_score": new_trust_score,
                    "auth_history": auth_history,
                    "total_emails_received": total_emails,
                    "verified_emails_count": verified_emails,
                    "last_verified_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                try:
                    self.supabase.table("sender_verification").update(update_data).eq("id", existing["id"]).execute()
                except Exception:
                    self.supabase.table("sender_verification").update(update_data).eq("id", existing["id"]).execute()

                try:
                    self.supabase.table("sender_verification").update({"is_verified": is_verified}).eq("id", existing["id"]).execute()
                except Exception:
                    pass

                return {
                    "status": "updated",
                    "sender_email": sender_email,
                    "trust_score": new_trust_score,
                    "is_verified": is_verified,
                }

            auth_history = [{
                "timestamp": datetime.now().isoformat(),
                "spf": spf_status,
                "dkim": dkim_status,
                "dmarc": dmarc_status,
                "score": auth_score,
            }]

            insert_data = {
                "user_id": user_id,
                "sender_email": sender_email,
                "sender_domain": sender_domain,
                "sender_name": sender_name,
                "trust_score": auth_score,
                "auth_history": auth_history,
                "total_emails_received": 1,
                "verified_emails_count": 1 if is_verified else 0,
                "last_verified_at": datetime.now().isoformat(),
            }

            result = self.supabase.table("sender_verification").insert(insert_data).execute()
            if result.data:
                try:
                    self.supabase.table("sender_verification").update({"is_verified": is_verified}).eq("id", result.data[0]["id"]).execute()
                except Exception:
                    pass

            return {
                "status": "created",
                "sender_email": sender_email,
                "trust_score": auth_score,
                "is_verified": is_verified,
            }
        except Exception as exc:
            print(f"[EmailAuthService] Error verifying sender: {exc}")
            return {"status": "error", "message": str(exc)}

    def get_sender_trust_info(self, user_id: str, sender_email: str) -> Dict:
        try:
            response = self.supabase.table("sender_verification").select("*").eq("user_id", user_id).eq("sender_email", sender_email).execute()
            if response.data:
                return response.data[0]
            return {
                "trust_score": 0,
                "is_verified": False,
                "is_trusted": False,
                "is_blocklisted": False,
                "total_emails_received": 0,
                "verified_emails_count": 0,
            }
        except Exception as exc:
            print(f"[EmailAuthService] Error getting sender trust info: {exc}")
            return {}

    def mark_sender_as_trusted(self, user_id: str, sender_email: str) -> Dict:
        try:
            response = self.supabase.table("sender_verification").select("id").eq("user_id", user_id).eq("sender_email", sender_email).execute()
            if not response.data:
                return {"status": "error", "message": "Sender not found"}

            sender_id = response.data[0]["id"]
            self.supabase.table("sender_verification").update({
                "is_trusted": True,
                "is_blocklisted": False,
                "updated_at": datetime.now().isoformat(),
            }).eq("id", sender_id).execute()

            return {"status": "ok", "message": "Sender marked as trusted"}
        except Exception as exc:
            print(f"[EmailAuthService] Error marking sender as trusted: {exc}")
            return {"status": "error", "message": str(exc)}

    def mark_sender_as_blocklisted(self, user_id: str, sender_email: str) -> Dict:
        try:
            response = self.supabase.table("sender_verification").select("id").eq("user_id", user_id).eq("sender_email", sender_email).execute()
            if not response.data:
                return {"status": "error", "message": "Sender not found"}

            sender_id = response.data[0]["id"]
            self.supabase.table("sender_verification").update({
                "is_blocklisted": True,
                "is_trusted": False,
                "updated_at": datetime.now().isoformat(),
            }).eq("id", sender_id).execute()

            return {"status": "ok", "message": "Sender marked as blocklisted"}
        except Exception as exc:
            print(f"[EmailAuthService] Error marking sender as blocklisted: {exc}")
            return {"status": "error", "message": str(exc)}

    def get_high_risk_senders(self, user_id: str, trust_score_threshold: int = 30) -> List[Dict]:
        try:
            response = self.supabase.table("sender_verification").select(
                "sender_email, sender_name, trust_score, total_emails_received, is_blocklisted"
            ).eq("user_id", user_id).lt("trust_score", trust_score_threshold).execute()
            return response.data if response.data else []
        except Exception as exc:
            print(f"[EmailAuthService] Error getting high-risk senders: {exc}")
            return []

    def get_verified_senders(self, user_id: str, limit: int = 50) -> List[Dict]:
        try:
            response = self.supabase.table("sender_verification").select(
                "sender_email, sender_name, trust_score, total_emails_received"
            ).eq("user_id", user_id).eq("is_verified", True).order("total_emails_received", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as exc:
            print(f"[EmailAuthService] Error getting verified senders: {exc}")
            return []


__all__ = ["EmailAuthService"]
