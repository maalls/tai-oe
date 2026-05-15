import json
import os
from pathlib import Path
from typing import Dict

from src.infrastructure.clients.supabase import get_supabase_service
from src.repository.opportunity import OpportunityRepository
import uuid
import yaml


class Quote:

    def __init__(self):
        self.supabase = get_supabase_service()
        self.opportunity_repository = OpportunityRepository()

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        try:
            print(f"[QuoteController][update] Updating document {document_id}", payload)

            doc_fields = payload.copy()

            # Update document header fields
            self.supabase.table("document").update({
                "title": doc_fields.get("title"),
                "currency": doc_fields.get("currency"),
            }).eq("id", document_id).execute()

            # Replace all lines: delete existing then re-insert
            print(f"[QuoteController][update] Deleting existing document lines for document_id: {document_id}")
            self.supabase.table("document_line").delete().eq("document_id", document_id).execute()

            lines_payload = payload.get("document_line", [])
            print(f"[QuoteController][update] Inserting {len(lines_payload)} lines")

            new_lines = []
            for idx, line in enumerate(lines_payload):
                print(f"[QuoteController][update] Processing line {idx}", line)

                brand = line.get("brand")
                if brand and not isinstance(brand, str):
                    raise ValueError(f"Brand must be a string, got {type(brand)} for line {idx}")

                client_discount_rate = self.safe_numeric(line.get("client_discount_rate"))

                new_lines.append({
                    "id": line.get("id") or str(uuid.uuid4()),
                    "document_id": document_id,
                    "position": idx + 1,
                    "description": line.get("description", ""),
                    "quantity": line.get("quantity", 0),
                    "unit_price_excl_tax": line.get("unit_price_excl_tax", 0),
                    "tax_rate": line.get("tax_rate", 0),
                    "sku": line.get("sku", ""),
                    "brand": brand or "",
                    "unit": line.get("unit", ""),
                    "discount_rate": self.safe_numeric(line.get("discount_rate")),
                    "client_discount_rate": client_discount_rate,
                })

            if new_lines:
                self.supabase.table("document_line").insert(new_lines).execute()

            # Compute and persist totals
            totals = self._compute_document_totals(lines_payload)
            print(f"[QuoteController][update] Computed totals: {totals}")
            self.supabase.table("document").update({
                "total_excl_tax": totals["total_excl_tax"],
                "total_tax": totals["total_tax"],
                "total_incl_tax": totals["total_incl_tax"],
            }).eq("id", document_id).execute()

            document = (
                self.supabase.table("document")
                .select("*, document_line(*)")
                .eq("id", document_id)
                .single()
                .execute()
                .data
            )
            return document
        except Exception as e:
            print(f"[QuoteController][update] Error updating quote: {e}")
            raise e
            
    def safe_numeric(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
        print(f"[QuoteController][update_line_from_product] Updating line from product: {product}")

        # If document is a SingleAPIResponse, extract .data
        if hasattr(document, "data") and isinstance(document.data, dict):
            document_dict = document.data
        else:
            document_dict = document

        if product.get("id"):
            response = self.supabase.table("document_line").select("*").eq("id", product.get("id")).single().execute()
            if not response.data:
                line = {
                    "document_id": document_dict.get("id"),
                }
            else:
                line = response.data
        else:
            line = {
                "document_id": document_dict.get("id"),
            }

        line['description'] = product.get("description")
        line['position'] = product.get("position")
        line["sku"] = product.get("sku")
        line['quantity'] = product.get("quantity")
        line['unit'] = product.get("unit")
        line['unit_price'] = product.get("price")
        line['unit_price_excl_tax'] = product.get("price")
        line['tax_rate'] = product.get("tax_rate", 20)
        line['discount_rate'] = product.get("discount_rate", 0)
        line['client_discount_rate'] = product.get("client_discount_rate", None)
        line['line_total_excl_tax'] = round(float(product.get("quantity", 1) or 1) * float(product.get("price", 0) or 0), 2)
        
    def _compute_document_totals(self, lines: list) -> Dict[str, float]:
        """Compute totals for a document from its lines, respecting both discount_rate and client_discount_rate.
        
        The unit_price_excl_tax from frontend already includes:
        - For net_price families: product.price (no markup, just family pricing)
        - For discount families: cost with family discount applied
        - For regular: cost with target margin applied
        
        Therefore, discount_rate is already baked into unit_price_excl_tax and should NOT be re-applied.
        Only client_discount_rate is applied as an additional customer-specific discount.
        
        Parameters
        ----------
        lines : list
            List of document_line dictionaries with quantity, unit_price_excl_tax, tax_rate, client_discount_rate
        
        Returns
        -------
        Dict[str, float]
            Dictionary with total_excl_tax, total_tax, total_incl_tax
        """
        total_excl = 0.0
        total_tax = 0.0
        
        for line in lines:
            try:
                qty = float(line.get("quantity", 1) or 1)
            except Exception:
                qty = 1.0
            
            try:
                unit_price = float(line.get("unit_price_excl_tax", 0) or 0)
            except Exception:
                unit_price = 0.0
            
            try:
                tax_rate = float(line.get("tax_rate", 20) or 20)
            except Exception:
                tax_rate = 20.0
            
            # Apply only client_discount_rate (additional customer discount)
            # discount_rate is already included in unit_price_excl_tax from frontend calculation
            client_discount_rate = 0.0
            if line.get("client_discount_rate"):
                try:
                    client_discount_rate = float(line.get("client_discount_rate")) / 100.0
                except Exception:
                    pass
            
            # Calculate line total: unit_price * qty * (1 - client_discount_rate)
            # unit_price_excl_tax already reflects all family discounts and markups
            line_total = qty * unit_price * (1.0 - client_discount_rate)
            total_excl += line_total
            total_tax += line_total * (tax_rate / 100.0)
        
        total_excl = round(total_excl, 2)
        total_tax = round(total_tax, 2)
        total_incl = round(total_excl + total_tax, 2)
        
        return {
            "total_excl_tax": total_excl,
            "total_tax": total_tax,
            "total_incl_tax": total_incl,
        }
    
    def _compute_totals(self, rfp_data: Dict) -> Dict[str, float]:
        return self.opportunity_repository._compute_totals(rfp_data)


