"""Email authentication verification service."""

from datetime import datetime
import json
from typing import Dict, List

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_service


class EmailAuthService:
    """Handle email authentication verification and trust scoring."""

    def __init__(self, db_handler: DatabaseHandler | None = None):
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = DatabaseHandler(
                database_service=create_database_service(
                    current_file=__file__,
                    require_postgres_password=True,
                )
            )
        return self.db_handler

    def _execute_raw_sql(self, query: str, params: tuple = None) -> bool:
        try:
            self._get_db_handler().execute_update(query, params or ())
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
            db_handler = self._get_db_handler()
            sender_domain = sender_email.split("@")[1] if "@" in sender_email else ""
            rows = db_handler.execute_dict_query(
                "SELECT * FROM sender_verification WHERE user_id = %s AND sender_email = %s LIMIT 1",
                (user_id, sender_email),
            )
            existing = rows[0] if rows else None

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
                    db_handler.execute_dict_query(
                        """
                        UPDATE sender_verification
                        SET trust_score = %s,
                            auth_history = %s::jsonb,
                            total_emails_received = %s,
                            verified_emails_count = %s,
                            last_verified_at = %s,
                            updated_at = %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (
                            update_data["trust_score"],
                            json.dumps(update_data["auth_history"]),
                            update_data["total_emails_received"],
                            update_data["verified_emails_count"],
                            update_data["last_verified_at"],
                            update_data["updated_at"],
                            existing["id"],
                        ),
                    )
                except Exception:
                    db_handler.execute_dict_query(
                        """
                        UPDATE sender_verification
                        SET trust_score = %s,
                            auth_history = %s::jsonb,
                            total_emails_received = %s,
                            verified_emails_count = %s,
                            last_verified_at = %s,
                            updated_at = %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (
                            update_data["trust_score"],
                            json.dumps(update_data["auth_history"]),
                            update_data["total_emails_received"],
                            update_data["verified_emails_count"],
                            update_data["last_verified_at"],
                            update_data["updated_at"],
                            existing["id"],
                        ),
                    )

                try:
                    db_handler.execute_update(
                        "UPDATE sender_verification SET is_verified = %s WHERE id = %s",
                        (is_verified, existing["id"]),
                    )
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

            result_rows = db_handler.execute_dict_query(
                """
                INSERT INTO sender_verification (
                    user_id,
                    sender_email,
                    sender_domain,
                    sender_name,
                    trust_score,
                    auth_history,
                    total_emails_received,
                    verified_emails_count,
                    last_verified_at
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                RETURNING id
                """,
                (
                    insert_data["user_id"],
                    insert_data["sender_email"],
                    insert_data["sender_domain"],
                    insert_data["sender_name"],
                    insert_data["trust_score"],
                    json.dumps(insert_data["auth_history"]),
                    insert_data["total_emails_received"],
                    insert_data["verified_emails_count"],
                    insert_data["last_verified_at"],
                ),
            )
            if result_rows:
                try:
                    db_handler.execute_update(
                        "UPDATE sender_verification SET is_verified = %s WHERE id = %s",
                        (is_verified, result_rows[0]["id"]),
                    )
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
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM sender_verification WHERE user_id = %s AND sender_email = %s LIMIT 1",
                (user_id, sender_email),
            )
            if rows:
                return rows[0]
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
            db_handler = self._get_db_handler()
            response = db_handler.execute_dict_query(
                "SELECT id FROM sender_verification WHERE user_id = %s AND sender_email = %s LIMIT 1",
                (user_id, sender_email),
            )
            if not response:
                return {"status": "error", "message": "Sender not found"}

            sender_id = response[0]["id"]
            db_handler.execute_update(
                """
                UPDATE sender_verification
                SET is_trusted = %s,
                    is_blocklisted = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (True, False, datetime.now().isoformat(), sender_id),
            )

            return {"status": "ok", "message": "Sender marked as trusted"}
        except Exception as exc:
            print(f"[EmailAuthService] Error marking sender as trusted: {exc}")
            return {"status": "error", "message": str(exc)}

    def mark_sender_as_blocklisted(self, user_id: str, sender_email: str) -> Dict:
        try:
            db_handler = self._get_db_handler()
            response = db_handler.execute_dict_query(
                "SELECT id FROM sender_verification WHERE user_id = %s AND sender_email = %s LIMIT 1",
                (user_id, sender_email),
            )
            if not response:
                return {"status": "error", "message": "Sender not found"}

            sender_id = response[0]["id"]
            db_handler.execute_update(
                """
                UPDATE sender_verification
                SET is_blocklisted = %s,
                    is_trusted = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (True, False, datetime.now().isoformat(), sender_id),
            )

            return {"status": "ok", "message": "Sender marked as blocklisted"}
        except Exception as exc:
            print(f"[EmailAuthService] Error marking sender as blocklisted: {exc}")
            return {"status": "error", "message": str(exc)}

    def get_high_risk_senders(self, user_id: str, trust_score_threshold: int = 30) -> List[Dict]:
        try:
            rows = self._get_db_handler().execute_dict_query(
                """
                SELECT sender_email, sender_name, trust_score, total_emails_received, is_blocklisted
                FROM sender_verification
                WHERE user_id = %s AND trust_score < %s
                """,
                (user_id, trust_score_threshold),
            )
            return rows or []
        except Exception as exc:
            print(f"[EmailAuthService] Error getting high-risk senders: {exc}")
            return []

    def get_verified_senders(self, user_id: str, limit: int = 50) -> List[Dict]:
        try:
            rows = self._get_db_handler().execute_dict_query(
                """
                SELECT sender_email, sender_name, trust_score, total_emails_received
                FROM sender_verification
                WHERE user_id = %s AND is_verified = %s
                ORDER BY total_emails_received DESC
                LIMIT %s
                """,
                (user_id, True, limit),
            )
            return rows or []
        except Exception as exc:
            print(f"[EmailAuthService] Error getting verified senders: {exc}")
            return []


__all__ = ["EmailAuthService"]
