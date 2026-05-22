"""Email database persistence helpers extracted from EmailRepository."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
from typing import Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_service


def _normalize_iso_datetime(date_string: str) -> Optional[str]:
    """Normalize ISO datetime strings for datetime.fromisoformat."""
    if not date_string:
        return None
    iso_candidate = date_string.strip().replace("Z", "+00:00")
    frac_match = re.match(r"^(.*T[0-9:]+)\.([0-9]+)(.*)$", iso_candidate)
    if frac_match:
        frac = frac_match.group(2)[:6].ljust(6, "0")
        iso_candidate = f"{frac_match.group(1)}.{frac}{frac_match.group(3)}"
    return iso_candidate


class EmailDatabaseHandler:
    """Handle email storage in Supabase database."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
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

    def get_profile_row(self, user_id: str, columns: str) -> Optional[Dict]:
        if not user_id:
            return None

        rows = self._get_db_handler().execute_dict_query(
            f"SELECT {columns} FROM profile WHERE id = %s LIMIT 1",
            (user_id,),
        )
        return rows[0] if rows else None

    def get_profile_column(self, user_id: str, column: str) -> Optional[str]:
        row = self.get_profile_row(user_id, column)
        if row:
            return row.get(column)
        return None

    def set_profile_column(self, user_id: str, column: str, value: Optional[str]) -> bool:
        rows = self._get_db_handler().execute_dict_query(
            f"UPDATE profile SET {column} = %s WHERE id = %s RETURNING id",
            (value, user_id),
        )
        return bool(rows)

    def clear_profile_column(self, user_id: str, column: str) -> bool:
        return self.set_profile_column(user_id, column, None)

    
    def _parse_email_date(self, date_string: str) -> Optional[str]:
        """Parse email date string to ISO format (UTC)."""
        if not date_string:
            raise ValueError("email_date is required but missing")

        try:
            dt = parsedate_to_datetime(date_string)
        except (TypeError, ValueError):
            iso_candidate = _normalize_iso_datetime(date_string)
            if not iso_candidate:
                raise ValueError(f"Unparseable email_date: '{date_string}'")
            dt = datetime.fromisoformat(iso_candidate)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()

    def store_email(
        self,
        user_id: str,
        provider: str,
        provider_message_id: str,
        subject: str,
        from_email: str,
        to_email: str,
        email_date: str,
        body_preview: str,
        body_full: Optional[str] = None,
        category: Optional[str] = None,
        classification_reason: Optional[str] = None,
        provider_thread_id: Optional[str] = None,
        provider_account_id: Optional[str] = None,
        provider_metadata: Optional[Dict] = None,
        from_name: Optional[str] = None,
        from_raw: Optional[str] = None,
        from_domain: Optional[str] = None,
        from_local: Optional[str] = None,
        from_is_valid: Optional[bool] = None,
        cc_email: Optional[str] = None,
        contact_id: Optional[str] = None,
        account_id: Optional[str] = None,
        spf_status: Optional[str] = None,
        dkim_status: Optional[str] = None,
        dmarc_status: Optional[str] = None,
        auth_score: Optional[int] = None,
        is_verified: Optional[bool] = None,
        auth_headers: Optional[Dict] = None,
    ) -> Dict:
        """Store an email in the database."""

        existing_classification = None
        try:
            existing_rows = self._get_db_handler().execute_dict_query(
                """
                SELECT category, classification_reason, is_classified, classified_at, category_suggestion, important
                FROM email
                WHERE user_id = %s AND provider = %s AND provider_message_id = %s
                LIMIT 1
                """,
                (user_id, provider, provider_message_id),
            )
            if existing_rows:
                existing_classification = existing_rows[0]
        except Exception:
            pass

        email_data = {
            "user_id": user_id,
            "provider": provider,
            "provider_message_id": provider_message_id,
            "provider_thread_id": provider_thread_id,
            "provider_account_id": provider_account_id,
            "subject": subject,
            "from_email": from_email,
            "from_name": from_name,
            "from_raw": from_raw,
            "from_domain": from_domain,
            "from_local": from_local,
            "from_is_valid": from_is_valid,
            "to_email": to_email,
            "cc_email": cc_email,
            "contact_id": contact_id,
            "account_id": account_id,
            "email_date": self._parse_email_date(email_date),
            "body_preview": body_preview,
            "body_full": body_full,
            "category": category,
            "classification_reason": classification_reason,
            "is_classified": category is not None,
            "classified_at": datetime.utcnow().isoformat() if category else None,
            "provider_metadata": provider_metadata or {},
            "fetched_at": datetime.utcnow().isoformat(),
            "spf_status": spf_status or "NONE",
            "dkim_status": dkim_status or "NONE",
            "dmarc_status": dmarc_status or "NONE",
            "auth_score": auth_score or 0,
            "is_verified": is_verified or False,
            "auth_headers": auth_headers or {},
            "sender_verified_at": datetime.utcnow().isoformat() if is_verified else None,
        }

        if existing_classification and existing_classification.get("is_classified") and not category:
            email_data["category"] = existing_classification.get("category")
            email_data["classification_reason"] = existing_classification.get("classification_reason")
            email_data["is_classified"] = True
            email_data["classified_at"] = existing_classification.get("classified_at")
            email_data["category_suggestion"] = existing_classification.get("category_suggestion")
            email_data["important"] = existing_classification.get("important")

        payload = dict(email_data)

        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO email (
                user_id,
                provider,
                provider_message_id,
                provider_thread_id,
                provider_account_id,
                subject,
                from_email,
                from_name,
                from_raw,
                from_domain,
                from_local,
                from_is_valid,
                to_email,
                cc_email,
                contact_id,
                account_id,
                email_date,
                body_preview,
                body_full,
                category,
                classification_reason,
                is_classified,
                classified_at,
                provider_metadata,
                fetched_at,
                spf_status,
                dkim_status,
                dmarc_status,
                auth_score,
                is_verified,
                auth_headers,
                sender_verified_at,
                category_suggestion,
                important,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s
            )
            ON CONFLICT (user_id, provider, provider_message_id)
            DO UPDATE SET
                provider_thread_id = EXCLUDED.provider_thread_id,
                provider_account_id = EXCLUDED.provider_account_id,
                subject = EXCLUDED.subject,
                from_email = EXCLUDED.from_email,
                from_name = EXCLUDED.from_name,
                from_raw = EXCLUDED.from_raw,
                from_domain = EXCLUDED.from_domain,
                from_local = EXCLUDED.from_local,
                from_is_valid = EXCLUDED.from_is_valid,
                to_email = EXCLUDED.to_email,
                cc_email = EXCLUDED.cc_email,
                contact_id = EXCLUDED.contact_id,
                account_id = EXCLUDED.account_id,
                email_date = EXCLUDED.email_date,
                body_preview = EXCLUDED.body_preview,
                body_full = EXCLUDED.body_full,
                category = COALESCE(EXCLUDED.category, email.category),
                classification_reason = COALESCE(EXCLUDED.classification_reason, email.classification_reason),
                is_classified = COALESCE(EXCLUDED.is_classified, email.is_classified),
                classified_at = COALESCE(EXCLUDED.classified_at, email.classified_at),
                provider_metadata = EXCLUDED.provider_metadata,
                fetched_at = EXCLUDED.fetched_at,
                spf_status = EXCLUDED.spf_status,
                dkim_status = EXCLUDED.dkim_status,
                dmarc_status = EXCLUDED.dmarc_status,
                auth_score = EXCLUDED.auth_score,
                is_verified = EXCLUDED.is_verified,
                auth_headers = EXCLUDED.auth_headers,
                sender_verified_at = EXCLUDED.sender_verified_at,
                category_suggestion = COALESCE(EXCLUDED.category_suggestion, email.category_suggestion),
                important = COALESCE(EXCLUDED.important, email.important),
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """,
            (
                payload["user_id"],
                payload["provider"],
                payload["provider_message_id"],
                payload["provider_thread_id"],
                payload["provider_account_id"],
                payload["subject"],
                payload["from_email"],
                payload["from_name"],
                payload["from_raw"],
                payload["from_domain"],
                payload["from_local"],
                payload["from_is_valid"],
                payload["to_email"],
                payload["cc_email"],
                payload["contact_id"],
                payload["account_id"],
                payload["email_date"],
                payload["body_preview"],
                payload["body_full"],
                payload["category"],
                payload["classification_reason"],
                payload["is_classified"],
                payload["classified_at"],
                json.dumps(payload["provider_metadata"]),
                payload["fetched_at"],
                payload["spf_status"],
                payload["dkim_status"],
                payload["dmarc_status"],
                payload["auth_score"],
                payload["is_verified"],
                json.dumps(payload["auth_headers"]),
                payload["sender_verified_at"],
                payload.get("category_suggestion"),
                payload.get("important", False),
                datetime.utcnow().isoformat(),
            ),
        )
        if rows:
            return {"success": True, "email_id": rows[0].get("id")}
        return {"success": False, "error": "Failed to insert email"}

    def add_labels(self, email_id: str, labels: List[Dict[str, str]]) -> Dict:
        """Add labels to an email."""

        label_data = [
            {
                "email_id": email_id,
                "provider_label_id": label.get("label_id", label.get("provider_label_id")),
                "label_name": label.get("label_name", label.get("name")),
            }
            for label in labels
        ]

        try:
            # Upsert to avoid duplicate constraint errors on (email_id, provider_label_id)
            rows = []
            for label in label_data:
                result = self._get_db_handler().execute_dict_query(
                    """
                    INSERT INTO email_labels (email_id, provider_label_id, label_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email_id, provider_label_id)
                    DO UPDATE SET label_name = EXCLUDED.label_name
                    RETURNING id
                    """,
                    (label["email_id"], label["provider_label_id"], label["label_name"]),
                )
                rows.extend(result)
            return {"success": True, "labels_added": len(rows)}
        except Exception as exc:  # pragma: no cover
            print(f"Error upserting labels: {exc}")
            return {"success": False, "error": str(exc)}

    def add_attachments(self, email_id: str, attachments: List[Dict[str, str]]) -> Dict:
        """Persist attachment metadata for an email."""
        attachment_data = []
        for attachment in attachments:
            provider_attachment_id = attachment.get("provider_attachment_id")
            if not provider_attachment_id:
                continue
            attachment_data.append(
                {
                    "email_id": email_id,
                    "provider_attachment_id": provider_attachment_id,
                    "filename": attachment.get("filename"),
                    "mime_type": attachment.get("mime_type"),
                    "size": attachment.get("size"),
                    "storage_path": attachment.get("storage_path"),
                }
            )

        if not attachment_data:
            return {"success": True, "attachments_added": 0}

        try:
            rows = []
            for attachment in attachment_data:
                result = self._get_db_handler().execute_dict_query(
                    """
                    INSERT INTO email_attachment (
                        email_id,
                        provider_attachment_id,
                        filename,
                        mime_type,
                        size,
                        storage_path
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email_id, provider_attachment_id)
                    DO UPDATE SET
                        filename = EXCLUDED.filename,
                        mime_type = EXCLUDED.mime_type,
                        size = EXCLUDED.size,
                        storage_path = EXCLUDED.storage_path
                    RETURNING id
                    """,
                    (
                        attachment["email_id"],
                        attachment["provider_attachment_id"],
                        attachment.get("filename"),
                        attachment.get("mime_type"),
                        attachment.get("size"),
                        attachment.get("storage_path"),
                    ),
                )
                rows.extend(result)
            return {"success": True, "attachments_added": len(rows)}
        except Exception as exc:  # pragma: no cover
            print(f"Error upserting attachments: {exc}")
            return {"success": False, "error": str(exc)}

    def get_labels(self, email_id: str) -> List[Dict]:
        """Get all labels for an email."""
        return self._get_db_handler().execute_dict_query(
            "SELECT label_name, provider_label_id FROM email_labels WHERE email_id = %s",
            (email_id,),
        )

    def get_email(self, email_id: str) -> Optional[Dict]:
        """Get a single email by ID for a user."""
        try:
            rows = self._get_db_handler().execute_dict_query(
                "SELECT * FROM email WHERE id = %s LIMIT 1",
                (email_id,),
            )
            return rows[0] if rows else None
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Error getting email: {exc}")
            return None

    def get_emails_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get emails for a user."""
        return self._get_db_handler().execute_dict_query(
            """
            SELECT *
            FROM email
            WHERE user_id = %s
            ORDER BY email_date DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset),
        )

    def get_emails_by_category(self, user_id: str, category: str, limit: int = 100) -> List[Dict]:
        """Get emails by category."""
        try:
            return self._get_db_handler().execute_dict_query(
                """
                SELECT *
                FROM email
                WHERE user_id = %s AND category = %s
                ORDER BY email_date DESC
                LIMIT %s
                """,
                (user_id, category, limit),
            )
        except Exception as exc:  # pragma: no cover
            print(f"Error getting emails by category: {exc}")
            return []

    def get_unclassified_emails(self, user_id: str, limit: int = 200) -> List[Dict]:
        """Return emails missing classification for a user."""
        try:
            data = self._get_db_handler().execute_dict_query(
                """
                SELECT id, subject, from_email, body_full, body_preview
                FROM email
                WHERE user_id = %s AND is_classified = FALSE
                ORDER BY email_date DESC
                LIMIT %s
                """,
                (user_id, limit),
            )

            if len(data) < limit:
                remaining = limit - len(data)
                null_rows = self._get_db_handler().execute_dict_query(
                    """
                    SELECT id, subject, from_email, body_full, body_preview
                    FROM email
                    WHERE user_id = %s AND is_classified IS NULL
                    ORDER BY email_date DESC
                    LIMIT %s
                    """,
                    (user_id, remaining),
                )
                data.extend(null_rows)

            return data
        except Exception as exc:  # pragma: no cover
            print(f"Error getting unclassified emails: {exc}")
            return []

    def get_latest_fetch_time(self, user_id: str, provider: str = "gmail") -> Optional[datetime]:
        """Get the timestamp of the last fetch from the provider."""
        rows = self._get_db_handler().execute_dict_query(
            "SELECT last_fetch_at FROM email_fetch_metadata WHERE user_id = %s AND provider = %s LIMIT 1",
            (user_id, provider),
        )
        if rows:
            fetch_at_str = rows[0].get("last_fetch_at")
            if fetch_at_str:
                normalized = _normalize_iso_datetime(fetch_at_str)
                return datetime.fromisoformat(normalized) if normalized else None
        return None
    
    def get_last_fetched_email_id(self, user_id: str, provider: str = "gmail") -> Optional[str]:
        """Get the provider_message_id of the most recently fetched email."""
        rows = self._get_db_handler().execute_dict_query(
            """
            SELECT provider_message_id
            FROM email
            WHERE user_id = %s AND provider = %s
            ORDER BY email_date DESC
            LIMIT 1
            """,
            (user_id, provider),
        )
        if rows:
            return rows[0].get("provider_message_id")
        return None

    def update_email_classification(
        self,
        email_uuid: str,
        user_id: str,
        category: str,
        category_suggestion: str,
        classification_reason: str,
        is_classified: bool = True,
        important: bool = False,
        classified_at: str = None,
    ) -> bool:
        """Update email classification fields."""
        try:
            update_data = {
                "category": category,
                "category_suggestion": category_suggestion,
                "classification_reason": classification_reason,
                "is_classified": is_classified,
                "important": important,
                "classified_at": classified_at or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            rows = self._get_db_handler().execute_dict_query(
                """
                UPDATE email
                SET category = %s,
                    category_suggestion = %s,
                    classification_reason = %s,
                    is_classified = %s,
                    important = %s,
                    classified_at = %s,
                    updated_at = %s
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (
                    update_data["category"],
                    update_data["category_suggestion"],
                    update_data["classification_reason"],
                    update_data["is_classified"],
                    update_data["important"],
                    update_data["classified_at"],
                    update_data["updated_at"],
                    email_uuid,
                    user_id,
                ),
            )
            return bool(rows)
        except Exception as exc:  # pragma: no cover
            print(f"Error updating email classification: {exc}")
            return False


