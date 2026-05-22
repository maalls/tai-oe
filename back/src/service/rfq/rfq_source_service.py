"""Service for RFQ source creation from multipart HTML/form payloads."""

from pathlib import Path
from typing import Dict
import time

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler
from src.lib.extractors.rfp_source_picker import pick_best_rfp_source
from src.lib.extractors.text_reader import extract_company_from_text
from src.lib.storage_paths import get_storage_dir
from src.repository.email_repository import EmailRepository
from src.repository.opportunity import OpportunityRepository


class RfqSourceService:
    """Encapsulates RFQ source creation previously implemented in API handlers."""

    def __init__(
        self,
        opportunity_repository: OpportunityRepository = None,
        email_repository: EmailRepository = None,
        db_handler: DatabaseHandler | None = None,
    ):
        self.opportunity_repository = opportunity_repository or OpportunityRepository()
        self.email_repository = email_repository or EmailRepository()
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def _find_account_id(self, account_name: str, contact_email: str | None) -> str | None:
        db_handler = self._get_db_handler()
        rows = db_handler.execute_dict_query(
            "SELECT id FROM account WHERE name = %s LIMIT 1",
            (account_name,),
        )
        if rows:
            return rows[0]["id"]

        if contact_email:
            rows = db_handler.execute_dict_query(
                "SELECT account_id FROM contact WHERE email = %s LIMIT 1",
                (contact_email,),
            )
            if rows:
                return rows[0]["account_id"]

        return None

    def _create_account(self, account_name: str) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            "INSERT INTO account (name) VALUES (%s) RETURNING id",
            (account_name,),
        )
        return rows[0]["id"] if rows else None

    def _create_opportunity(self, user_id: str | None, opportunity_name: str, account_id: str) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO opportunity (owner_user_id, name, stage, status, source, account_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, opportunity_name, "RFP_IN_PROGRESS", "OPEN", "user_form", account_id),
        )
        return rows[0]["id"] if rows else None

    def _create_document(
        self,
        opportunity_id: str,
        doc_type: str,
        title: str,
        storage_key: str,
        user_id: str | None,
    ) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO document (opportunity_id, type, status, title, currency, channel, storage_key, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (opportunity_id, doc_type, "RECEIVED", title, "EUR", "OTHER", storage_key, user_id),
        )
        return rows[0]["id"] if rows else None

    def _link_opportunity_source_document(self, opportunity_id: str, document_id: str) -> None:
        self._get_db_handler().execute_update(
            "UPDATE opportunity SET source_reference_id = %s, source = %s WHERE id = %s",
            (document_id, "rfp_upload", opportunity_id),
        )

    def _find_opportunity_account_id(self, opportunity_id: str) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            "SELECT account_id FROM opportunity WHERE id = %s LIMIT 1",
            (opportunity_id,),
        )
        return rows[0]["account_id"] if rows else None

    def _find_contact_id(self, account_id: str, email: str) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            "SELECT id FROM contact WHERE email = %s AND account_id = %s LIMIT 1",
            (email, account_id),
        )
        return rows[0]["id"] if rows else None

    def _create_contact(self, account_id: str, contact_data: Dict[str, str]) -> str | None:
        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO contact (account_id, name, email, phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                account_id,
                contact_data.get("name") or contact_data.get("email"),
                contact_data["email"],
                contact_data.get("phone"),
            ),
        )
        return rows[0]["id"] if rows else None

    def _create_opportunity_participant(self, opportunity_id: str, contact_id: str) -> None:
        self._get_db_handler().execute_update(
            """
            INSERT INTO opportunity_participant (opportunity_id, contact_id, role)
            VALUES (%s, %s, %s)
            """,
            (opportunity_id, contact_id, "BUYER"),
        )

    def create_rfq_source_from_html_body(
        self,
        opportunity_id: str,
        body: bytes,
        content_type: str,
        user_id: str | None = None,
    ) -> Dict:
        form_data, error = self.get_form(body, content_type)
        if error:
            return error

        message_text = str(form_data.get("message", "") or form_data.get("text", "") or "")
        uploaded_file = form_data.get("file")
        provided_opportunity_name = str(form_data.get("opportunity_name", "") or "")

        if not message_text.strip() and not uploaded_file:
            return {"status": "error", "message": "Message text or attachment is required"}
        if not message_text.strip() and uploaded_file:
            message_text = ""

        rfp_data = {"products": [], "contact": {}}
        message_is_placeholder = message_text.strip() == ""
        if message_text.strip() and not message_is_placeholder:
            rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(message_text)
            company_data = extract_company_from_text(self.email_repository._clean_email_body(message_text))
            if isinstance(company_data, dict) and company_data:
                rfp_data["contact"] = company_data

        opportunity_name = provided_opportunity_name or rfp_data.get("title") or "RFP from Source Page"
        account_name = rfp_data.get("contact", {}).get("company_name") if isinstance(rfp_data.get("contact"), dict) else None

        if opportunity_id == "new":
            if not account_name:
                contact_data = rfp_data.get("contact", {})
                account_name = contact_data.get("company_name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = contact_data.get("name") if isinstance(contact_data, dict) else None
                if not account_name:
                    account_name = "Unknown Company"

            contact_email = rfp_data.get("contact", {}).get("email") if isinstance(rfp_data.get("contact"), dict) else None
            account_id = self._find_account_id(account_name=account_name, contact_email=contact_email)

            if not account_id:
                account_id = self._create_account(account_name)

            if not account_id:
                return {"status": "error", "message": "Failed to create or find account"}

            new_opportunity_id = self._create_opportunity(user_id, opportunity_name, account_id)
            if not new_opportunity_id:
                return {"status": "error", "message": "Failed to create opportunity"}
            opportunity_id = new_opportunity_id

        storage_dir = get_storage_dir("rfp_upload")
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())

        text_filename = f"{timestamp}_message.txt"
        text_file_path = storage_dir / text_filename
        text_file_path.write_text(message_text, encoding="utf-8")

        document_id = self._create_document(
            opportunity_id=opportunity_id,
            doc_type="RFP",
            title=opportunity_name,
            storage_key=text_filename,
            user_id=user_id,
        )
        if not document_id:
            return {"status": "error", "message": "Failed to create document"}

        attachment_doc_id = None
        attachment_file_path = None
        attachment_content_type = None
        if uploaded_file and isinstance(uploaded_file, dict):
            filename = uploaded_file.get("filename")
            file_content = uploaded_file.get("content")
            attachment_content_type = uploaded_file.get("content_type")
            if filename and file_content:
                safe_filename = f"{timestamp}_attachment_{filename}"
                file_path = storage_dir / safe_filename
                file_path.write_bytes(file_content)
                attachment_file_path = file_path
                attachment_doc_data = {
                    "opportunity_id": opportunity_id,
                    "type": "ATTACHMENT",
                    "status": "RECEIVED",
                    "title": f"Attachment: {filename}",
                    "currency": "EUR",
                    "channel": "OTHER",
                    "storage_key": safe_filename,
                    "created_by": user_id,
                }
                attachment_doc_id = self._create_document(
                    opportunity_id=attachment_doc_data["opportunity_id"],
                    doc_type=attachment_doc_data["type"],
                    title=attachment_doc_data["title"],
                    storage_key=attachment_doc_data["storage_key"],
                    user_id=attachment_doc_data["created_by"],
                )

        self._link_opportunity_source_document(opportunity_id=opportunity_id, document_id=document_id)

        contact_data = rfp_data.get("contact", {})
        if isinstance(contact_data, dict) and contact_data.get("email"):
            try:
                account_id = self._find_opportunity_account_id(opportunity_id)
                if account_id:
                    contact_id = self._find_contact_id(account_id=account_id, email=contact_data["email"])
                    if not contact_id:
                        contact_id = self._create_contact(account_id=account_id, contact_data=contact_data)
                    if contact_id:
                        self._create_opportunity_participant(opportunity_id=opportunity_id, contact_id=contact_id)
            except Exception as exc:
                print(f"[RfqSourceService] Warning: Failed to create contact/participant: {exc}")

        pdf_candidates = []
        if attachment_file_path and (attachment_content_type or "").lower().startswith("application/pdf"):
            pdf_candidates.append(
                {
                    "id": attachment_doc_id,
                    "filename": uploaded_file.get("filename") if isinstance(uploaded_file, dict) else None,
                    "path": attachment_file_path,
                }
            )

        picker_text = "" if message_is_placeholder else message_text
        try:
            selection = pick_best_rfp_source(picker_text, pdf_candidates)
        except Exception as exc:
            print(f"[RfqSourceService] RFQ source selection failed: {exc}")
            return {
                "status": "error",
                "message": "RFQ extraction failed during source selection",
                "details": str(exc),
            }
        selected_content = selection.get("content") or ("" if message_is_placeholder else message_text)
        pre_extracted = selection.get("extracted_data")
        if pre_extracted is None and (rfp_data.get("products") or rfp_data.get("contact") or rfp_data.get("title")):
            pre_extracted = rfp_data

        if selected_content:
            quote_result = self.opportunity_repository.handle_generate_quote_with_content(
                opportunity_id=opportunity_id,
                content=selected_content,
                user_id=user_id,
                pre_extracted_data=pre_extracted,
            )
        else:
            quote_result = self.opportunity_repository.handle_generate_quote_for_opportunity(
                opportunity_id=opportunity_id,
                user_id=user_id,
            )

        return {
            "status": "ok",
            "message": "RFQ source created successfully",
            "opportunity_id": opportunity_id,
            "document_id": document_id,
            "attachment_doc_id": attachment_doc_id,
            "quote": quote_result,
            "opportunity": {"id": opportunity_id},
        }

    def get_form(self, body: bytes, content_type: str):
        boundary = self._extract_boundary(content_type)
        if not boundary:
            return None, {"status": "error", "message": "Invalid content type"}
        return self._parse_multipart(body, boundary), None

    @staticmethod
    def _extract_boundary(content_type: str):
        if "boundary=" not in content_type:
            return None
        boundary = content_type.split("boundary=")[1]
        return boundary.strip('"\'')

    @staticmethod
    def _parse_multipart(body: bytes, boundary: str) -> Dict:
        form_data = {}
        parts = body.split(f"--{boundary}".encode())
        for part in parts[1:-1]:
            if not part.strip():
                continue
            try:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1:
                    header_end = part.find(b"\n\n")
                    if header_end == -1:
                        continue
                    content_start = header_end + 2
                else:
                    content_start = header_end + 4

                headers = part[:header_end].decode("utf-8", errors="ignore")
                content = part[content_start:]
                if content.endswith(b"\r\n"):
                    content = content[:-2]
                elif content.endswith(b"\n"):
                    content = content[:-1]

                if "Content-Disposition" in headers:
                    disp_line = [h for h in headers.split("\n") if "Content-Disposition" in h][0]
                    if 'name="' in disp_line:
                        name_start = disp_line.find('name="') + 6
                        name_end = disp_line.find('"', name_start)
                        name = disp_line[name_start:name_end]
                        if "filename=" in disp_line:
                            filename_start = disp_line.find('filename="') + 10
                            filename_end = disp_line.find('"', filename_start)
                            filename = disp_line[filename_start:filename_end]
                            file_content_type = "application/octet-stream"
                            for header_line in headers.split("\n"):
                                if "Content-Type:" in header_line:
                                    file_content_type = header_line.split("Content-Type:")[1].strip()
                            form_data[name] = {
                                "filename": filename,
                                "content": content,
                                "content_type": file_content_type,
                                "size": len(content),
                            }
                        else:
                            form_data[name] = content.decode("utf-8", errors="ignore")
            except Exception as exc:
                print(f"[RfqSourceService] Error parsing part: {exc}")
                continue
        return form_data
