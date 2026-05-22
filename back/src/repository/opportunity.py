from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
import os

from flask import json

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_service
from src.lib.extractors.rfp_source_picker import pick_best_rfp_source
from src.lib.extractors.text_reader import extract_rfp_from_text
from src.repository.email_repository import EmailRepository
from pathlib import Path


class OpportunityRepository:
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

    def _select_best_family(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        direct_net_price_family = product.get("direct_net_price_family") if isinstance(product, dict) else None
        if isinstance(direct_net_price_family, dict):
            family_type = str(direct_net_price_family.get("type") or "").lower()
            if family_type == "net_price":
                return direct_net_price_family

        links = product.get("product_family") or []
        if not isinstance(links, list):
            return None

        best_discount_family: Optional[Dict[str, Any]] = None
        for link in links:
            family = (link or {}).get("family") if isinstance(link, dict) else None
            if not isinstance(family, dict):
                continue

            family_type = str(family.get("type") or "").lower()
            if family_type == "net_price":
                return family

            if family_type != "discount":
                continue

            current_discount = float(family.get("discount") or 0)
            best_discount = float((best_discount_family or {}).get("discount") or float("-inf"))
            if current_discount > best_discount:
                best_discount_family = family

        return best_discount_family

    def _build_lines_from_rfp_data(self, rfp_data: Dict[str, Any], db_source) -> tuple:
        """Build document lines list and totals from extracted RFP data.

        Fetches product metadata from DB, computes ``client_discount_rate`` for
        each line, and returns ``(lines, totals)`` where ``lines`` does NOT yet
        have ``document_id`` set (caller must add it before inserting).
        """
        product_meta_by_sku: Dict[str, Any] = {}
        skus = [
            str((p or {}).get("sku") or "").strip()
            for p in (rfp_data.get("products", []) or [])
            if str((p or {}).get("sku") or "").strip()
        ]
        unique_skus = list(dict.fromkeys(skus))
        if unique_skus:
            try:
                if hasattr(db_source, "execute_dict_query"):
                    products = db_source.execute_dict_query(
                        """
                        SELECT
                            p.sku,
                            p.price,
                            CASE
                                WHEN b.id IS NULL THEN '{}'::jsonb
                                ELSE jsonb_build_object('target_margin', b.target_margin)
                            END AS brand,
                            COALESCE(
                                (
                                    SELECT jsonb_agg(jsonb_build_object('family', to_jsonb(f.*)))
                                    FROM product_family pf
                                    LEFT JOIN family f ON f.id = pf.family_id
                                    WHERE pf.product_id = p.id
                                ),
                                '[]'::jsonb
                            ) AS product_family
                        FROM product p
                        LEFT JOIN brand b ON b.id = p.brand_id
                        WHERE p.sku = ANY(%s)
                        """,
                        (unique_skus,),
                    )
                else:
                    product_resp = (
                        db_source.table("product")
                        .select("sku, price, brand(*), product_family(family(*))")
                        .in_("sku", unique_skus)
                        .execute()
                    )
                    products = product_resp.data or []

                for prod in (products or []):
                    sku = str((prod or {}).get("sku") or "").strip()
                    if sku:
                        product_meta_by_sku[sku] = prod

                # Net-price families are keyed by family.product_code, not always by product_family links.
                if hasattr(db_source, "execute_dict_query"):
                    net_price_families = db_source.execute_dict_query(
                        "SELECT * FROM family WHERE product_code = ANY(%s) AND LOWER(type) = 'net_price'",
                        (unique_skus,),
                    )
                else:
                    net_price_resp = (
                        db_source.table("family")
                        .select("*")
                        .in_("product_code", unique_skus)
                        .ilike("type", "net_price")
                        .execute()
                    )
                    net_price_families = net_price_resp.data or []

                for family in (net_price_families or []):
                    sku = str((family or {}).get("product_code") or "").strip()
                    if not sku:
                        continue
                    if sku not in product_meta_by_sku:
                        continue
                    product_meta_by_sku[sku]["direct_net_price_family"] = family
            except Exception as e:
                print(f"[OpportunityRepository] Warning: failed to load product metadata for discount init: {e}")

        lines: list = []
        total_excl = 0.0
        total_tax = 0.0

        for idx, product in enumerate(rfp_data.get("products", []), start=1):
            try:
                qty_val = float(product.get("quantity", 1) or 1)
            except Exception:
                qty_val = 1.0

            sku = str(product.get("sku") or "").strip()
            product_meta = product_meta_by_sku.get(sku)

            extracted_price = product.get("price", 0)
            try:
                price_val = float(extracted_price or 0)
            except Exception:
                price_val = 0.0

            # Persist a concrete unit price at draft generation time.
            # If extraction doesn't provide one, fallback to catalog product price now
            # (instead of doing it later during save/pdf generation).
            if price_val <= 0 and isinstance(product_meta, dict):
                try:
                    price_val = float(product_meta.get("price") or 0)
                except Exception:
                    price_val = 0.0

            try:
                tax_rate = float(product.get("tax_rate", 20) or 20)
            except Exception:
                tax_rate = 20.0

            client_discount_rate = self._compute_client_discount_rate(product_meta)
            discount_ratio = (client_discount_rate or 0.0) / 100.0

            line_total = round(qty_val * price_val * (1 - discount_ratio), 2)
            total_excl += line_total
            total_tax += line_total * (tax_rate / 100.0)

            lines.append({
                "position": idx,
                "sku": product.get("sku"),
                "brand": product.get("manufacturer"),
                "description": product.get("description") or product.get("title") or "",
                "quantity": qty_val,
                "unit": product.get("unit", "U"),
                "unit_price_excl_tax": price_val,
                "tax_rate": tax_rate,
                "line_total_excl_tax": line_total,
                "client_discount_rate": client_discount_rate,
            })

        totals = {
            "total_excl_tax": round(total_excl, 2),
            "total_tax": round(total_tax, 2),
            "total_incl_tax": round(total_excl + total_tax, 2),
        }
        return lines, totals

    def _compute_client_discount_rate(self, product: Optional[Dict[str, Any]]) -> Optional[float]:
        """Compute initial client discount from target margin using backend pricing metadata.

        Mirrors frontend `targetDiscount(item)` logic:
        discount = (1 - purchased_price / ((1 - target_margin) * list_price)) * 100
        """
        if not isinstance(product, dict):
            return None

        list_price = float(product.get("price") or 0)
        if list_price <= 0:
            return None

        best_family = self._select_best_family(product)
        brand = product.get("brand") if isinstance(product.get("brand"), dict) else {}

        family_type = str((best_family or {}).get("type") or "").lower()
        if family_type == "net_price":
            purchased_price = float((best_family or {}).get("net_price") or 0)
        else:
            family_discount = float((best_family or {}).get("discount") or 0)
            purchased_price = list_price * (1 - family_discount / 100.0)

        target_margin = (best_family or {}).get("target_margin")
        if target_margin is None:
            target_margin = brand.get("target_margin") if isinstance(brand, dict) else 0

        try:
            target_margin = float(target_margin or 0)
        except Exception:
            target_margin = 0.0

        denominator = (1 - target_margin / 100.0) * list_price
        if denominator <= 0:
            return None

        discount = (1 - (purchased_price / denominator)) * 100.0
        if not isinstance(discount, float):
            return None

        return round(discount, 3)

    def create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        """Create a manual opportunity from a name string."""
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}

        trimmed_name = (name or "").strip()
        if not trimmed_name:
            return {"status": "error", "message": "Missing opportunity name"}

        db_handler = self._get_db_handler()
        try:
            account_name = "Unknown Company"
            account_id = None

            account_rows = db_handler.execute_dict_query(
                "SELECT id FROM account WHERE name = %s LIMIT 1",
                (account_name,),
            )
            if account_rows:
                account_id = account_rows[0].get("id")
            else:
                created_account = db_handler.execute_dict_query(
                    "INSERT INTO account (name) VALUES (%s) RETURNING id",
                    (account_name,),
                )
                if created_account:
                    account_id = created_account[0].get("id")

            if not account_id:
                return {"status": "error", "message": "Failed to resolve default account"}

            insert_data = {
                "owner_user_id": user_id,
                "account_id": account_id,
                "name": trimmed_name,
                "stage": "NEW_LEAD",
                "status": "OPEN",
                "source": "manual",
            }
            created_rows = db_handler.execute_dict_query(
                """
                INSERT INTO opportunity (owner_user_id, account_id, name, stage, status, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    insert_data["owner_user_id"],
                    insert_data["account_id"],
                    insert_data["name"],
                    insert_data["stage"],
                    insert_data["status"],
                    insert_data["source"],
                ),
            )

            created = created_rows[0] if created_rows else None
            return {"status": "ok", "opportunity": created}
        except Exception as e:
            return {"status": "error", "message": f"Error creating opportunity: {str(e)}"}

    def search_opportunities(self, user_id: str, source_reference_id: str = None, name: str = None) -> Dict:
        """Search opportunities with optional filtering.
        
        Parameters
        ----------
        user_id : str
            User ID for authorization
        source_reference_id : str, optional
            Filter by source reference ID (e.g., email ID)
        
        Returns
        -------
        Dict
            Response with list of opportunities
        """
        db_handler = self._get_db_handler()
        
        try:
            query = "SELECT * FROM opportunity WHERE 1 = 1"
            params: list = []
            
            # Filter by source_reference_id if provided
            if source_reference_id:
                try:
                    UUID(source_reference_id)
                except Exception:
                    return {
                        "status": "error",
                        "message": "Invalid source_reference_id. Expected a UUID.",
                    }
                query += " AND source_reference_id = %s"
                params.append(source_reference_id)

            if name:
                query += " AND name ILIKE %s"
                params.append(f"%{name}%")
            
            # Order by created date descending
            query += " ORDER BY created_at DESC"
            rows = db_handler.execute_dict_query(query, tuple(params))
            
            return {
                "status": "ok",
                "opportunities": rows or [],
                "count": len(rows or [])
            }
        except Exception as e:
            return {"status": "error", "message": f"Error searching opportunities: {str(e)}"}

    def delete_opportunities(self, opportunity_ids: list, user_id: str = None) -> Dict:
        """Delete one or more opportunities and their related data.
        
        Parameters
        ----------
        opportunity_ids : list
            List of opportunity IDs to delete
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with deletion status and count
        """
        db_handler = self._get_db_handler()
        
        if not opportunity_ids:
            return {"status": "error", "message": "No opportunity IDs provided"}
        
        try:
            deleted_count = 0
            errors = []
            
            for opportunity_id in opportunity_ids:
                try:
                    # Verify opportunity exists
                    opp_rows = db_handler.execute_dict_query(
                        "SELECT id FROM opportunity WHERE id = %s LIMIT 1",
                        (opportunity_id,),
                    )
                    if not opp_rows:
                        errors.append(f"Opportunity not found: {opportunity_id}")
                        continue
                    
                    # Delete opportunity (cascade will handle related records)
                    deleted = db_handler.execute_update(
                        "DELETE FROM opportunity WHERE id = %s",
                        (opportunity_id,),
                    )
                    if deleted > 0:
                        deleted_count += 1
                    else:
                        errors.append(f"Failed to delete {opportunity_id}: no rows affected")
                except Exception as e:
                    errors.append(f"Error deleting {opportunity_id}: {str(e)}")
            
            response = {
                "status": "ok" if deleted_count > 0 else "error",
                "deleted_count": deleted_count,
                "total_requested": len(opportunity_ids)
            }
            
            if deleted_count > 0:
                response["message"] = f"Successfully deleted {deleted_count} opportunity/ies"
            
            if errors:
                response["errors"] = errors
            
            return response
        except Exception as e:
            return {"status": "error", "message": f"Error deleting opportunities: {str(e)}"}
    
    def delete_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Delete a single opportunity and its related data (backward compatibility wrapper).
        
        Parameters
        ----------
        opportunity_id : str
            The opportunity ID to delete
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with deletion status
        """
        result = self.delete_opportunities([opportunity_id], user_id)
        # Convert batch response to single response format for backward compatibility
        if result.get('status') == 'ok' and result.get('deleted_count', 0) > 0:
            return {"status": "ok", "message": "Opportunity deleted successfully"}
        else:
            errors = result.get('errors', [])
            message = errors[0] if errors else result.get('message', 'Failed to delete opportunity')
            return {"status": "error", "message": message}

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None, pre_extracted_data: Dict = None) -> Dict:
        """Generate a quote draft using custom content (e.g., from PDF attachment).
        
        Similar to handle_generate_quote_for_opportunity but uses provided content
        instead of loading from email/document source.
        
        Parameters
        ----------
        opportunity_id : str
            The opportunity ID
        content : str
            Text content to extract RFP data from
        user_id : str, optional
            User ID for authorization and audit trail
        pre_extracted_data : Dict, optional
            Pre-extracted RFP data (e.g., from pick_best_rfp_source).
            If provided, skips LLM extraction and enriches directly.
        """
        db_handler = self._get_db_handler()

        try:
            # 1) Load opportunity
            opp_rows = db_handler.execute_dict_query(
                "SELECT * FROM opportunity WHERE id = %s LIMIT 1",
                (opportunity_id,),
            )
            opportunity = opp_rows[0] if opp_rows else None
            if not opportunity:
                return {"status": "error", "message": f"Opportunity not found: {opportunity_id}"}

            if not content:
                return {
                    "status": "error",
                    "message": "No content provided for quote generation",
                }

            # 2) Extract and enrich RFP/quote data via shared helper
            rfp_data = self._extract_and_enrich_rfp_data(content, pre_extracted_data=pre_extracted_data)
            lines, totals = self._build_lines_from_rfp_data(rfp_data, db_handler)

            document_data = {
                "opportunity_id": opportunity_id,
                "type": "QUOTE",
                "status": "DRAFT",
                "title": rfp_data.get("title") or opportunity.get("name") or "Quote",
                "external_ref": f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "currency": opportunity.get("currency") or "EUR",
                "channel": "EMAIL" if opportunity.get("source") == "email" else "OTHER",
                "storage_key": None,
                "total_excl_tax": totals["total_excl_tax"],
                "total_tax": totals["total_tax"],
                "total_incl_tax": totals["total_incl_tax"],
                "created_by": user_id,
            }

            doc_rows = db_handler.execute_dict_query(
                """
                INSERT INTO document (
                    opportunity_id, type, status, title, external_ref, currency,
                    channel, storage_key, total_excl_tax, total_tax, total_incl_tax, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    document_data["opportunity_id"],
                    document_data["type"],
                    document_data["status"],
                    document_data["title"],
                    document_data["external_ref"],
                    document_data["currency"],
                    document_data["channel"],
                    document_data["storage_key"],
                    document_data["total_excl_tax"],
                    document_data["total_tax"],
                    document_data["total_incl_tax"],
                    document_data["created_by"],
                ),
            )
            if not doc_rows:
                return {"status": "error", "message": "Document insert returned no data"}

            document = doc_rows[0]
            document_id = document.get("id")

            # Insert specialized quote row
            try:
                db_handler.execute_update(
                    "INSERT INTO quote (document_id) VALUES (%s)",
                    (document_id,),
                )
            except Exception as quote_err:
                print(f"[OpportunityRepository] Warning: failed to insert quote specialization: {quote_err}")

            # Insert document lines from products
            if lines:
                try:
                    for line in lines:
                        db_handler.execute_update(
                            """
                            INSERT INTO document_line (
                                document_id, position, sku, brand, description,
                                quantity, unit, unit_price_excl_tax, tax_rate,
                                line_total_excl_tax, client_discount_rate
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                document_id,
                                line.get("position"),
                                line.get("sku"),
                                line.get("brand"),
                                line.get("description"),
                                line.get("quantity"),
                                line.get("unit"),
                                line.get("unit_price_excl_tax"),
                                line.get("tax_rate"),
                                line.get("line_total_excl_tax"),
                                line.get("client_discount_rate"),
                            ),
                        )
                except Exception as line_err:
                    print(f"[OpportunityRepository] Warning: failed to insert document lines: {line_err}")

            return {
                "status": "ok",
                "document": {
                    "id": document_id,
                    "pdf_filename": None,
                    "totals": totals,
                    "title": document.get("title"),
                    "currency": document.get("currency"),
                },
                "draft": rfp_data,
            }

        except Exception as e:  # noqa: BLE001
            print(f"[OpportunityRepository] Error generating quote with custom content: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Generate a quote draft (no PDF yet) for a given opportunity.

        Steps:
        1. Load opportunity (name, currency, source email reference)
        2. Fetch the source email body when available
        3. Extract RFP data via the existing LLM pipeline
        4. Persist document + lines (DRAFT) without generating PDF
        """
        db_handler = self._get_db_handler()

        try:
            # 1) Load opportunity
            opp_rows = db_handler.execute_dict_query(
                "SELECT * FROM opportunity WHERE id = %s LIMIT 1",
                (opportunity_id,),
            )
            opportunity = opp_rows[0] if opp_rows else None
            if not opportunity:
                return {"status": "error", "message": f"Opportunity not found: {opportunity_id}"}

            # 2) Load source content (email or RFP document)
            content = ""
            pre_extracted_data = None  # Will be set if pick_best_rfp_source is called
            source_ref_id = opportunity.get("source_reference_id") if isinstance(opportunity, dict) else None
            
            # Try to load from email (prefer PDF attachment if it has more products)
            if opportunity.get("source") == "email" and source_ref_id:
                try:
                    repo = EmailRepository()
                    email = repo.db_handler.get_email(source_ref_id)
                    if not email:
                        try:
                            email_rows = db_handler.execute_dict_query(
                                "SELECT * FROM email WHERE provider_message_id = %s AND user_id = %s LIMIT 1",
                                (source_ref_id, user_id),
                            )
                            email = email_rows[0] if email_rows else None
                        except Exception as lookup_err:
                            print(f"[OpportunityRepository] Warning: email lookup by provider_message_id failed: {lookup_err}")
                    email_body = ""
                    if email:
                        if user_id and email.get("user_id") != user_id:
                            raise PermissionError("Unauthorized access to email source")
                        email_body = email.get("body_full") or email.get("body_preview") or ""

                    pdf_candidates = []
                    try:
                        attachments = db_handler.execute_dict_query(
                            "SELECT id, filename, mime_type, storage_path FROM email_attachment WHERE email_id = %s",
                            (source_ref_id,),
                        )
                        pdf_candidates = [
                            {
                                "id": att.get("id"),
                                "filename": att.get("filename"),
                                "path": Path(att.get("storage_path")) if att.get("storage_path") else None,
                            }
                            for att in (attachments or [])
                            if (att.get("mime_type") or "").lower().startswith("application/pdf")
                        ]
                    except Exception as e:
                        print(f"[OpportunityRepository] Warning: could not load email PDF attachments: {e}")

                    selection = pick_best_rfp_source(email_body, pdf_candidates)
                    content = selection.get("content", email_body)
                    pre_extracted_data = selection.get("extracted_data")  # Cache to avoid re-extraction
                except Exception as e:  # noqa: BLE001 - operational warning
                    print(f"[OpportunityRepository] Warning: could not load email body for quote generation: {e}")
            
            # Try to load from RFP document (prefer PDF attachment if it has more products)
            elif opportunity.get("source") == "rfp_upload" and source_ref_id:
                try:
                    print("[OpportunityRepository] Loading RFP document for opportunity quote generation")
                    doc_rows = db_handler.execute_dict_query(
                        "SELECT * FROM document WHERE id = %s LIMIT 1",
                        (source_ref_id,),
                    )
                    if doc_rows:
                        document = doc_rows[0]
                        base_text = ""
                        
                        # Get content from storage_key if available
                        if document.get("storage_key"):
                            storage_key = document.get("storage_key")
                            # Files for rfp_upload are stored in var/storage/rfp_uploads/
                            base_storage = Path(__file__).parent.parent.parent / "var" / "storage" / "rfp_uploads"
                            file_path = base_storage / storage_key
                            print(f"[OpportunityRepository] Loading RFP document storage file: {file_path}")
                            if file_path.exists():
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        base_text = f.read()
                                        print(f"[OpportunityRepository] Loaded {len(base_text)} chars from storage file")
                                except Exception as read_err:
                                    print(f"[OpportunityRepository] Warning: could not read storage file {file_path}: {read_err}")
                            else:
                                print(f"[OpportunityRepository] Warning: Storage file not found: {file_path}")
                        else:
                            print("[OpportunityRepository] No storage_key found for RFP document")
                            
                        # Look for PDF attachments linked to this opportunity
                        pdf_candidates = []
                        try:
                            attachments = db_handler.execute_dict_query(
                                "SELECT id, title, storage_key FROM document WHERE opportunity_id = %s AND type = %s",
                                (opportunity_id, "ATTACHMENT"),
                            )
                            for att in (attachments or []):
                                name = att.get("title") or att.get("storage_key") or ""
                                # Check if this is a PDF by name
                                if (name.lower().endswith(".pdf") or "pdf" in name.lower()) and att.get("storage_key"):
                                    # Attachments are also in rfp_uploads directory
                                    base_storage = Path(__file__).parent.parent.parent / "var" / "storage" / "rfp_uploads"
                                    pdf_path = base_storage / att.get("storage_key")
                                    pdf_candidates.append({
                                        "id": att.get("id"),
                                        "filename": name.replace("Attachment: ", ""),
                                        "path": pdf_path,
                                    })
                        except Exception as e:
                            print(f"[OpportunityRepository] Warning: could not load RFP attachment list: {e}")

                        selection = pick_best_rfp_source(base_text, pdf_candidates)
                        content = selection.get("content", base_text)
                        pre_extracted_data = selection.get("extracted_data")  # Cache to avoid re-extraction
                except Exception as e:
                    print(f"[OpportunityRepository] Warning: could not load RFP document content for quote generation: {e}")

            if not content:
                return {
                    "status": "error",
                    "message": "No content available to generate the quote (neither email nor RFP document found)",
                }

            # 3) Extract, enrich, and build lines with discounts
            rfp_data = self._extract_and_enrich_rfp_data(content, pre_extracted_data=pre_extracted_data)
            lines, totals = self._build_lines_from_rfp_data(rfp_data, db_handler)

            # 4) Persist document + lines (no PDF yet)
            document_data = {
                "opportunity_id": opportunity_id,
                "type": "QUOTE",
                "status": "DRAFT",
                "title": rfp_data.get("title") or opportunity.get("name") or "Quote",
                "external_ref": f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "currency": opportunity.get("currency") or "EUR",
                "channel": "EMAIL" if opportunity.get("source") == "email" else "OTHER",
                "storage_key": None,
                "total_excl_tax": totals["total_excl_tax"],
                "total_tax": totals["total_tax"],
                "total_incl_tax": totals["total_incl_tax"],
                "created_by": user_id,
            }

            doc_rows = db_handler.execute_dict_query(
                """
                INSERT INTO document (
                    opportunity_id, type, status, title, external_ref, currency,
                    channel, storage_key, total_excl_tax, total_tax, total_incl_tax, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    document_data["opportunity_id"],
                    document_data["type"],
                    document_data["status"],
                    document_data["title"],
                    document_data["external_ref"],
                    document_data["currency"],
                    document_data["channel"],
                    document_data["storage_key"],
                    document_data["total_excl_tax"],
                    document_data["total_tax"],
                    document_data["total_incl_tax"],
                    document_data["created_by"],
                ),
            )
            if not doc_rows:
                return {"status": "error", "message": "Document insert returned no data"}

            document = doc_rows[0]
            document_id = document.get("id")

            # Insert specialized quote row
            try:
                db_handler.execute_update(
                    "INSERT INTO quote (document_id) VALUES (%s)",
                    (document_id,),
                )
            except Exception as quote_err:
                print(f"[OpportunityRepository] Warning: failed to insert quote specialization: {quote_err}")

            if lines:
                try:
                    for line in lines:
                        db_handler.execute_update(
                            """
                            INSERT INTO document_line (
                                document_id, position, sku, brand, description,
                                quantity, unit, unit_price_excl_tax, tax_rate,
                                line_total_excl_tax, client_discount_rate
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                document_id,
                                line.get("position"),
                                line.get("sku"),
                                line.get("brand"),
                                line.get("description"),
                                line.get("quantity"),
                                line.get("unit"),
                                line.get("unit_price_excl_tax"),
                                line.get("tax_rate"),
                                line.get("line_total_excl_tax"),
                                line.get("client_discount_rate"),
                            ),
                        )
                except Exception as line_err:
                    print(f"[OpportunityRepository] Warning: failed to insert document lines: {line_err}")

            return {
                "status": "ok",
                "document": {
                    "id": document_id,
                    "pdf_filename": None,
                    "totals": totals,
                    "title": document.get("title"),
                    "currency": document.get("currency"),
                },
                "draft": rfp_data,
            }

        except Exception as e:  # noqa: BLE001
            print(f"[OpportunityRepository] Error generating quote for opportunity: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _extract_and_enrich_rfp_data(self, text: str, pre_extracted_data: Dict = None) -> Dict:
        """Extract RFP data from text and normalize product pricing fields.

        This is a common helper used by both RFP upload and RFQ source creation
        to avoid code duplication. It extracts RFP data using LLM and ensures
        all product pricing fields are present even when no enrichment source
        is available.

        Parameters
        ----------
        text : str
            Text content to extract RFP data from
        pre_extracted_data : Dict, optional
            Pre-extracted RFP data (e.g., from pick_best_rfp_source).
            If provided, skips LLM extraction and enriches directly.

        Returns
        -------
        Dict
            RFP data with extracted products and enriched pricing
        """
        # Clean the text first
        text_clean = EmailRepository._clean_email_body(text)

        # Use pre-extracted data only if it has useful content
        # Otherwise extract using LLM (avoid using empty cache)
        has_useful_content = pre_extracted_data and (
            (pre_extracted_data.get('products') and len(pre_extracted_data.get('products', [])) > 0) or
            (pre_extracted_data.get('contact') and any(pre_extracted_data.get('contact').values()))
        )

        if has_useful_content:
            pre_count = len(pre_extracted_data.get('products', []) or []) if isinstance(pre_extracted_data, dict) else 0
            print(f"[OpportunityRepository] Using pre_extracted_data (products={pre_count}), skipping LLM extraction")
            rfp_data = pre_extracted_data
        else:
            print("[OpportunityRepository] No usable pre_extracted_data, running LLM extraction")
            quote_llm_timeout = int(os.getenv("QUOTE_LLM_TIMEOUT", os.getenv("RFQ_LLM_TIMEOUT", "600")))
            rfp_data = extract_rfp_from_text(text_clean, timeout_seconds=quote_llm_timeout)
            if isinstance(rfp_data, list):
                rfp_data = {"products": rfp_data, "contact": {}}
            elif isinstance(rfp_data, str):
                try:
                    parsed = json.loads(rfp_data)
                    if isinstance(parsed, dict):
                        rfp_data = parsed
                    elif isinstance(parsed, list):
                        rfp_data = {"products": parsed, "contact": {}}
                    else:
                        rfp_data = {"products": [], "contact": {}}
                except Exception:
                    rfp_data = {"products": [], "contact": {}}
            elif not isinstance(rfp_data, dict):
                rfp_data = {"products": [], "contact": {}}

        # Normalize field names: part_number -> sku
        for product in rfp_data.get('products', []) or []:
            if 'part_number' in product and 'sku' not in product:
                product['sku'] = product.pop('part_number')

        for product in rfp_data.get('products', []) or []:
            product['price_found'] = bool(product.get('price'))
            product['price'] = product.get('price')

        return rfp_data
    

    def _compute_totals(self, rfp_data: Dict) -> Dict[str, float]:
        """Compute totals for a quote from RFP data."""
        products = rfp_data.get("products", []) if isinstance(rfp_data, dict) else []

        total_excl = 0.0
        total_tax = 0.0

        for product in products:
            try:
                qty = float(product.get("quantity", 1) or 1)
            except Exception:
                qty = 1.0

            try:
                price = float(product.get("price", 0) or 0)
            except Exception:
                price = 0.0

            try:
                raw_tax_rate = product.get("tax_rate", 20)
                if raw_tax_rate is None or raw_tax_rate == "":
                    raw_tax_rate = 20
                tax_rate = float(raw_tax_rate)
            except Exception:
                tax_rate = 20.0

            line_total = qty * price
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