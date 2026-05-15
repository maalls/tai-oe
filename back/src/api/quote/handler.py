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


