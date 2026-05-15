"""Application service for quote operations."""

import uuid
from typing import Dict

from src.infrastructure.clients.supabase import get_supabase_service
from src.repository.opportunity import OpportunityRepository


class QuoteService:
    """Service that encapsulates quote business operations."""

    def __init__(self, supabase=None, opportunity_repository=None):
        self.supabase = supabase or get_supabase_service()
        self.opportunity_repository = opportunity_repository or OpportunityRepository()

    def update(self, document_id: str, payload: dict, user_id: str = None) -> Dict:
        del user_id
        try:
            print(f"[QuoteController][update] Updating document {document_id}", payload)

            doc_fields = payload.copy()

            self.supabase.table("document").update({
                "title": doc_fields.get("title"),
                "currency": doc_fields.get("currency"),
            }).eq("id", document_id).execute()

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

    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        print(f"[QuoteController][update_line_from_product] Updating line from product: {product}")

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

        line["description"] = product.get("description")
        line["position"] = product.get("position")
        line["sku"] = product.get("sku")
        line["quantity"] = product.get("quantity")
        line["unit"] = product.get("unit")
        line["unit_price"] = product.get("price")
        line["unit_price_excl_tax"] = product.get("price")
        line["tax_rate"] = product.get("tax_rate", 20)
        line["discount_rate"] = product.get("discount_rate", 0)
        line["client_discount_rate"] = product.get("client_discount_rate", None)
        line["line_total_excl_tax"] = round(float(product.get("quantity", 1) or 1) * float(product.get("price", 0) or 0), 2)

    def _compute_document_totals(self, lines: list) -> Dict[str, float]:
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

            client_discount_rate = 0.0
            if line.get("client_discount_rate"):
                try:
                    client_discount_rate = float(line.get("client_discount_rate")) / 100.0
                except Exception:
                    pass

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
