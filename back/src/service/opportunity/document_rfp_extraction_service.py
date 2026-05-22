"""Service for extracting RFP data from stored documents."""

import os
from typing import Callable, Dict

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler


class DocumentRfpExtractionService:
    """Extract and enrich RFP payloads from document storage files."""

    def __init__(
        self,
        db_handler: DatabaseHandler | None = None,
        supabase=None,
        storage_path_resolver: Callable[[str, str], object] = None,
        clean_email_body: Callable[[str], str] = None,
        extract_rfp: Callable[[str], Dict] = None,
        extract_company: Callable[[str], Dict] = None,
        enrich_rfp: Callable[[str, Dict], Dict] = None,
        extract_pdf_text: Callable[[object], str] = None,
        extract_rfp_pdf_vision: Callable[[object], Dict] = None,
    ):
        self.db_handler = db_handler
        self.supabase = supabase
        self.storage_path_resolver = storage_path_resolver
        self.clean_email_body = clean_email_body
        self.extract_rfp = extract_rfp
        self.extract_company = extract_company
        self.enrich_rfp = enrich_rfp
        self.extract_pdf_text = extract_pdf_text
        self.extract_rfp_pdf_vision = extract_rfp_pdf_vision

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def _get_document(self, document_id: str) -> Dict | None:
        rows = self._get_db_handler().execute_dict_query(
            "SELECT * FROM document WHERE id = %s LIMIT 1",
            (document_id,),
        )
        return rows[0] if rows else None

    def extract_from_document(self, document_id: str) -> Dict:
        try:
            document = self._get_document(document_id)
            if not document:
                return {"status": "error", "message": "Document not found"}
            storage_key = document.get("storage_key")

            if not storage_key:
                return {"status": "error", "message": "Document has no storage key"}

            file_path = self.storage_path_resolver("rfp_upload", storage_key)
            if not file_path.exists():
                return {"status": "error", "message": "Document file not found in storage"}

            configured_extraction_mode = (os.getenv("QUOTE_EXTRACTION_MODE", "text") or "text").strip().lower()
            extraction_mode = configured_extraction_mode
            if extraction_mode not in {"text", "vision"}:
                extraction_mode = "text"

            file_ext = file_path.suffix.lower()
            used_extraction_mode = "text"
            rfp_data = None
            if file_ext == ".pdf":
                try:
                    extractor = self.extract_pdf_text
                    if extractor is None:
                        from src.lib.extractors.pdf import extract_text

                        extractor = extract_text
                    content = extractor(file_path)
                    if not content:
                        return {"status": "error", "message": "Could not extract text from PDF"}
                except Exception as exc:
                    print(f"[DocumentRfpExtractionService] Error extracting PDF: {exc}")
                    return {"status": "error", "message": f"Failed to extract PDF: {str(exc)}"}

                if extraction_mode == "vision":
                    try:
                        used_extraction_mode = "vision"
                        vision_extractor = self.extract_rfp_pdf_vision
                        if vision_extractor is None:
                            from src.lib.extractors.text_reader import extract_rfp_from_pdf_vision

                            vision_extractor = extract_rfp_from_pdf_vision
                        rfp_data = vision_extractor(file_path)
                    except Exception as exc:
                        print(f"[DocumentRfpExtractionService] Error extracting RFP with vision: {exc}")
                        return {
                            "status": "error",
                            "message": f"Failed to extract RFP data with vision: {str(exc)}",
                        }
            else:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception as exc:
                    print(f"[DocumentRfpExtractionService] Error reading text file: {exc}")
                    return {"status": "error", "message": f"Failed to read file: {str(exc)}"}

            print(
                "[DocumentRfpExtractionService] Quote extraction mode "
                f"configured='{configured_extraction_mode}' effective='{extraction_mode}' used='{used_extraction_mode}' "
                f"file_ext='{file_ext}' document_id='{document_id}'"
            )

            if not content or not content.strip():
                return {"status": "error", "message": "Document is empty"}

            message_clean = self.clean_email_body(content)

            try:
                if not isinstance(rfp_data, dict):
                    rfp_data = self.extract_rfp(message_clean)
                if not isinstance(rfp_data, dict):
                    rfp_data = {"products": [], "contact": {}}

                try:
                    company_data = self.extract_company(message_clean)
                    if isinstance(company_data, dict) and company_data:
                        rfp_data["contact"] = company_data
                        print(f"[DocumentRfpExtractionService] Extracted company data: {company_data}")
                except Exception as exc:
                    print(f"[DocumentRfpExtractionService] Warning: Failed to extract company data: {exc}")

                rfp_data = self.enrich_rfp(message_clean, rfp_data)

                print(f"[DocumentRfpExtractionService] Extracted and enriched RFP data from document {document_id}")
                return {
                    "status": "ok",
                    "data": rfp_data,
                    "document_id": document_id,
                }
            except Exception as exc:
                print(f"[DocumentRfpExtractionService] Error extracting RFP: {exc}")
                return {"status": "error", "message": f"Failed to extract RFP data: {str(exc)}"}

        except Exception as exc:
            print(f"[DocumentRfpExtractionService] Error in extract_from_document: {exc}")
            return {"status": "error", "message": str(exc)}
