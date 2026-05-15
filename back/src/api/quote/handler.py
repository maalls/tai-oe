import json
import os
from pathlib import Path
from typing import Dict

from src.service.quote.service import QuoteService
import yaml


class Quote:

    def __init__(self, quote_service: QuoteService = None):
        self.quote_service = quote_service or QuoteService()

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        return self.quote_service.update(document_id=document_id, payload=payload, user_id=user_id)
            
    def safe_numeric(self, value):
        return self.quote_service.safe_numeric(value)

    def handle_quote_submit(self, payload):
        """Handle quote submission and generate PDF.
        
        Parameters
        ----------
        body : bytes
            Raw JSON body with RFP data
        content_type : str
            Content-Type header value
        
        Returns
        -------
        Dict
            Response with status, message, and PDF filename
        """
        try:
            # Parse JSON body
            payload = json.loads(body.decode('utf-8'))
            
            # Validate structure
            if not payload or 'products' not in payload:
                return {
                    "status": "error",
                    "message": "Invalid quote data: missing products"
                }
            
            # Generate PDF
            pdf_filename = self._generate_quote_pdf(payload)
            
            # Log the received quote
            print(f"[QuoteController] Quote received with {len(payload.get('products', []))} products")
            print(f"[QuoteController] PDF generated: {pdf_filename}")
            
            return {
                "status": "ok",
                "message": "Quote received and PDF generated successfully",
                "pdf_filename": pdf_filename
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON in request body"
            }
        except Exception as e:
            print(f"[QuoteController] Error in handle_quote_submit: {e}")
            return {
                "status": "error",
                "message": f"Error processing quote: {str(e)}"
            }
        
    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        self.quote_service.update_line_from_product(document=document, product=product)
        
    def _compute_document_totals(self, lines: list) -> Dict[str, float]:
        return self.quote_service._compute_document_totals(lines)
    
    def _compute_totals(self, rfp_data: Dict) -> Dict[str, float]:
        return self.quote_service._compute_totals(rfp_data)

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        base_storage = Path("var/storage")
        source_map = {
            "rfp_upload": "rfp_uploads",
            "email": "emails",
            "quote": "quotes",
            "invoice": "invoices",
            "attachment": "attachments",
        }
        subdir = source_map.get(source, source)
        return base_storage / subdir

    @staticmethod
    def _get_storage_path(source: str, filename: str) -> Path:
        return Quote._get_storage_dir(source) / filename

    def handle_list_quotes(self) -> Dict:
        """List all generated quote files."""
        try:
            assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            pdf_files = sorted(
                [f.name for f in assets_dir.glob("quote_*.pdf")],
                reverse=True,
            )

            return {
                "status": "ok",
                "quotes": pdf_files,
                "total": len(pdf_files),
            }
        except Exception as e:  # noqa: BLE001
            print(f"[QuoteController] Error listing quotes: {e}")
            return {
                "status": "error",
                "message": f"Error listing quotes: {str(e)}",
            }

    def handle_get_quote_file(self, filename: str) -> bytes:
        """Retrieve a quote PDF file from storage."""
        try:
            if not filename.startswith("quote_") or not filename.endswith(".pdf"):
                raise ValueError(f"Invalid filename format: {filename}")

            pdf_path = self._get_storage_path("quote", filename)

            if not pdf_path.exists():
                legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                legacy_pdf_path = legacy_assets_dir / filename

                if legacy_pdf_path.exists():
                    pdf_path = legacy_pdf_path
                else:
                    raise FileNotFoundError(f"Quote file not found: {filename}")

            return pdf_path.read_bytes()
        except FileNotFoundError:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[QuoteController] Error retrieving quote: {e}")
            raise FileNotFoundError(f"Error retrieving quote: {str(e)}")


