"""Document-related request handlers."""

from pathlib import Path
import time
import uuid
from datetime import datetime
from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service
from src.lib.extractors.text_reader import extract_company_from_text, extract_rfp_from_text
from src.service.opportunity.document_content_service import DocumentContentService
from src.service.opportunity.document_rfp_extraction_service import DocumentRfpExtractionService


class DocumentHandlers:
    """Handle document-related API requests."""

    def __init__(
        self,
        supabase=None,
        storage_dir_resolver: Callable = None,
        storage_path_resolver: Callable = None,
        clean_email_body: Callable = None,
        enrich_rfp: Callable = None,
    ):
        self.supabase = supabase or get_supabase_service()
        self.storage_dir_resolver = storage_dir_resolver
        self.storage_path_resolver = storage_path_resolver
        self.clean_email_body = clean_email_body
        self.enrich_rfp = enrich_rfp
        self._document_content_service = None
        self._document_rfp_extraction_service = None

    @property
    def document_content_service(self) -> DocumentContentService:
        if self._document_content_service is None:
            self._document_content_service = DocumentContentService(
                supabase=self.supabase,
                storage_dir_resolver=self.storage_dir_resolver,
            )
        return self._document_content_service

    @property
    def document_rfp_extraction_service(self) -> DocumentRfpExtractionService:
        if self._document_rfp_extraction_service is None:
            self._document_rfp_extraction_service = DocumentRfpExtractionService(
                supabase=self.supabase,
                storage_path_resolver=self.storage_path_resolver,
                clean_email_body=self.clean_email_body,
                extract_rfp=extract_rfp_from_text,
                extract_company=extract_company_from_text,
                enrich_rfp=self.enrich_rfp,
            )
        return self._document_rfp_extraction_service

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_content_service.update_document_content(
            document_id=document_id,
            content=content,
        )

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        _ = user_id
        return self.document_rfp_extraction_service.extract_from_document(document_id=document_id)

    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete a quote document and its related data."""
        _ = user_id
        try:
            doc_resp = (
                self.supabase.table("document")
                .select("id, type, storage_key, opportunity_id")
                .eq("id", document_id)
                .maybe_single()
                .execute()
            )
            document = doc_resp.data if doc_resp and doc_resp.data else None

            if not document:
                return {"status": "error", "message": "Quote document not found"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "Document is not a quote"}

            self._delete_storage_file(storage_type="quote", storage_key=document.get("storage_key"))

            delete_resp = self.supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete quote: {delete_resp.error}"}

            return {"status": "ok", "message": "Quote deleted successfully"}

        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Error deleting quote document {document_id}: {e}")
            return {
                "status": "error",
                "message": f"Error deleting quote: {str(e)}",
            }

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete any document and its related data."""
        _ = user_id
        try:
            doc_resp = (
                self.supabase.table("document")
                .select("id, type, storage_key, opportunity_id")
                .eq("id", document_id)
                .maybe_single()
                .execute()
            )
            document = doc_resp.data if doc_resp and doc_resp.data else None

            if not document:
                return {"status": "error", "message": "Document not found"}

            doc_type = str(document.get("type") or "").lower()
            storage_type = "quote" if doc_type == "quote" else "invoice" if doc_type == "invoice" else "rfp_upload"
            self._delete_storage_file(storage_type=storage_type, storage_key=document.get("storage_key"))

            delete_resp = self.supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete document: {delete_resp.error}"}

            return {
                "status": "ok",
                "message": f"{document.get('type', 'Document')} deleted successfully",
            }

        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Error deleting document {document_id}: {e}")
            return {
                "status": "error",
                "message": f"Error deleting document: {str(e)}",
            }

    def _delete_storage_file(self, storage_type: str, storage_key: str) -> None:
        if not storage_key:
            return

        try:
            if self.storage_path_resolver is not None:
                storage_path = self.storage_path_resolver(storage_type, storage_key)
                if storage_path.exists():
                    storage_path.unlink()
                    return

            legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            legacy_path = legacy_assets_dir / storage_key
            if legacy_path.exists():
                legacy_path.unlink()
        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Warning: Could not delete file {storage_key}: {e}")

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str) -> Dict:
        """Handle chat attachment upload: store file and create document record."""
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        if not opportunity_id:
            return {"status": "error", "message": "Missing opportunity_id"}

        form_data, error = self.get_form(body, content_type)
        if error:
            return error

        uploaded_file = form_data.get("file")
        if not uploaded_file or not isinstance(uploaded_file, dict):
            return {"status": "error", "message": "No file provided"}

        filename = uploaded_file.get("filename")
        file_content = uploaded_file.get("content")
        mime_type = uploaded_file.get("content_type")
        file_size = uploaded_file.get("size")

        if not filename or not file_content:
            return {"status": "error", "message": "Invalid file payload"}

        try:
            unique_name = f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"
            storage_key = unique_name

            storage_dir = (
                self.storage_dir_resolver("attachment")
                if self.storage_dir_resolver is not None
                else Path("var/storage/attachments")
            )
            storage_dir.mkdir(parents=True, exist_ok=True)
            (storage_dir / storage_key).write_bytes(file_content)

            doc_data = {
                "opportunity_id": opportunity_id,
                "type": "ATTACHMENT",
                "status": "RECEIVED",
                "title": f"Chat Attachment: {filename}",
                "currency": "EUR",
                "channel": "OTHER",
                "storage_key": storage_key,
                "created_by": user_id,
            }

            doc_result = self.supabase.table("document").insert(doc_data).execute()
            if not doc_result.data:
                return {"status": "error", "message": "Failed to create document"}

            document_id = doc_result.data[0]["id"]

            try:
                self.supabase.table("opportunity").update({"updated_at": datetime.now().isoformat()}).eq(
                    "id", opportunity_id
                ).execute()
            except Exception as e:  # noqa: BLE001
                print(f"[DocumentHandlers] Warning: failed to touch opportunity {opportunity_id}: {e}")

            return {
                "status": "ok",
                "document_id": document_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": file_size,
                "storage_key": storage_key,
            }
        except Exception as e:  # noqa: BLE001
            print(f"[DocumentHandlers] Error uploading chat attachment: {e}")
            return {"status": "error", "message": f"Upload failed: {str(e)}"}

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
                            part_content_type = "application/octet-stream"
                            for header_line in headers.split("\n"):
                                if "Content-Type:" in header_line:
                                    part_content_type = header_line.split("Content-Type:")[1].strip()
                            form_data[name] = {
                                "filename": filename,
                                "content": content,
                                "content_type": part_content_type,
                                "size": len(content),
                            }
                        else:
                            form_data[name] = content.decode("utf-8", errors="ignore")
            except Exception as e:  # noqa: BLE001
                print(f"[DocumentHandlers] Error parsing multipart part: {e}")
                continue
        return form_data
