"""Service for extracting RFP data from stored documents."""

from typing import Callable, Dict

from src.infrastructure.clients.supabase import get_supabase_service


class DocumentRfpExtractionService:
    """Extract and enrich RFP payloads from document storage files."""

    def __init__(
        self,
        supabase=None,
        storage_path_resolver: Callable[[str, str], object] = None,
        clean_email_body: Callable[[str], str] = None,
        extract_rfp: Callable[[str], Dict] = None,
        extract_company: Callable[[str], Dict] = None,
        enrich_rfp: Callable[[str, Dict], Dict] = None,
        extract_pdf_text: Callable[[object], str] = None,
    ):
        self.supabase = supabase or get_supabase_service()
        self.storage_path_resolver = storage_path_resolver
        self.clean_email_body = clean_email_body
        self.extract_rfp = extract_rfp
        self.extract_company = extract_company
        self.enrich_rfp = enrich_rfp
        self.extract_pdf_text = extract_pdf_text

    def extract_from_document(self, document_id: str) -> Dict:
        try:
            doc_result = self.supabase.table("document").select("*").eq("id", document_id).single().execute()
            if not doc_result.data:
                return {"status": "error", "message": "Document not found"}

            document = doc_result.data
            storage_key = document.get("storage_key")

            if not storage_key:
                return {"status": "error", "message": "Document has no storage key"}

            file_path = self.storage_path_resolver("rfp_upload", storage_key)
            if not file_path.exists():
                return {"status": "error", "message": "Document file not found in storage"}

            file_ext = file_path.suffix.lower()
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
            else:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except Exception as exc:
                    print(f"[DocumentRfpExtractionService] Error reading text file: {exc}")
                    return {"status": "error", "message": f"Failed to read file: {str(exc)}"}

            if not content or not content.strip():
                return {"status": "error", "message": "Document is empty"}

            message_clean = self.clean_email_body(content)

            try:
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
