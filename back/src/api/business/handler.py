"""Business-related request handlers for RFP and other business operations."""

from typing import Dict, Optional
import json
import hashlib
import os
import uuid
import time
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from io import BytesIO
from weasyprint import HTML
from html.parser import HTMLParser

from src.text.reader import extract_company_from_text, extract_rfp_from_text
from src.text.rfp_source_picker import pick_best_rfp_source
from src.api.email.handler import EmailHandlers
from src.controller.rfq_handler import RfqHandlers
from src.infrastructure.factory import ServiceFactory
from src.repository.email_repository import EmailRepository
from src.supabase.supabase_client import get_supabase_service
from src.controller.opportunity.opportunity import Opportunity as OpportunityController
from src.lib.email.html_parser import Parser
from src.repository.opportunity import OpportunityRepository


class BusinessHandlers:
    """Handle business-related API requests."""
    
    def __init__(self, service_factory: ServiceFactory = None):
        """Initialize business handlers."""
        self.email_handlers = EmailHandlers()
        self.email_repository = EmailRepository()
        self.service_factory = service_factory or ServiceFactory()
        self.opportunity_repository = OpportunityRepository()
        self.rfq_handlers = RfqHandlers(
            service_factory=self.service_factory,
            email_repository=self.email_repository,
            opportunity_repository=self.opportunity_repository,
        )
        self.supabase = get_supabase_service()
        self.opportunity_controller = OpportunityController()

    @staticmethod
    def _clean_email_body(email_body: str, max_length: int = 3000) -> str:
        return EmailRepository._clean_email_body(email_body, max_length=max_length)
    
    def _extract_and_enrich_rfp_data(self, text: str) -> Dict:
        return self.opportunity_repository._extract_and_enrich_rfp_data(text)

    @staticmethod
    def _normalize_account_address(account: Dict) -> Dict[str, str]:
        """Return a stable address shape for PDF templates.

        The database has used both `address_line1/address_line2` and
        `street_address`, so we normalize all known variants here and keep
        missing fields empty to avoid rendering `None` in the PDF.
        """
        account = account or {}
        street_address = (
            account.get('street_address')
            or account.get('address_line1')
            or account.get('address1')
            or ''
        )
        address_line2 = account.get('address_line2') or account.get('address2') or ''
        city = account.get('city') or ''
        postal_code = account.get('postal_code') or ''
        country_name = account.get('country_name') or account.get('country') or ''

        return {
            'street_address': street_address,
            'address_line1': account.get('address_line1') or street_address,
            'address_line2': address_line2,
            'city': city,
            'postal_code': postal_code,
            'country_name': country_name,
        }

    def getForm(self, body: bytes, content_type: str):
        boundary = self._extract_boundary(content_type)
        if not boundary:
            return None, {"status": "error", "message": "Invalid content type"}
        return self._parse_multipart(body, boundary), None
    
    def handle_rfp_upload(self, body: bytes, content_type: str) -> Dict:
        try:
            # Parse multipart form data
            form_data, error = self.getForm(body, content_type)
            if error:
                return error
            
            # Extract text fields (title, description, etc.)
            text_fields = {
                key: value for key, value in form_data.items()
                if not isinstance(value, dict) or 'filename' not in value
            }
            
            # Extract file attachments
            files = {
                key: value for key, value in form_data.items()
                if isinstance(value, dict) and 'filename' in value
            }
            
            print(f"[BusinessHandlers] Received RFP upload:")
            print(f"  Text fields: {list(text_fields.keys())}", text_fields.keys())
            print(f"  Files: {[f.get('filename') for f in files.values()]}")
            # Cache behavior
            message_text = text_fields.get('message', '') or ''
            cache_flag = str(text_fields.get('cache', 'false')).lower() in ("1", "true", "yes", "on")

            cache_hit = False
            rfp_data = None
            cache_dir = Path("var/storage/rfp_cache")
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

            # Create cache key from message content
            key = hashlib.sha256(message_text.encode('utf-8')).hexdigest()
            cache_file = cache_dir / f"{key}.json"

            if cache_flag and cache_file.exists():
                try:
                    rfp_data = json.loads(cache_file.read_text(encoding='utf-8'))
                    cache_hit = True
                    print(f"[BusinessHandlers] Cache hit for key {key}")
                except Exception as e:
                    print(f"[BusinessHandlers] Cache read error: {e}")

            if rfp_data is None:

                rfp_data = extract_rfp_from_text(message_text)

                # Normalize field names: part_number → sku
                for product in rfp_data.get('products', []) or []:
                    if 'part_number' in product and 'sku' not in product:
                        product['sku'] = product.pop('part_number')

                # Preserve pricing fields without vector enrichment.
                for product in rfp_data.get('products', []) or []:
                    product['price_found'] = bool(product.get('price'))
                    product['price'] = product.get('price')


                if cache_flag:
                    try:
                        cache_file.write_text(json.dumps(rfp_data, ensure_ascii=False, indent=2), encoding='utf-8')
                        print(f"[BusinessHandlers] Cached result under key {key}")
                    except Exception as e:
                        print(f"[BusinessHandlers] Cache write error: {e}")
            return {
                "status": "ok",
                "message": "RFP received successfully",
                "text_fields": list(text_fields.keys()),
                "files": [f.get('filename') for f in files.values() if isinstance(f, dict)],
                "total_files": len(files),
                "extracted_rfp": rfp_data,
                "cache": "hit" if cache_hit else ("miss" if cache_flag else "off")
            }
        
        except Exception as e:
            print(f"[BusinessHandlers] Error processing RFP: {e}")
            return {
                "status": "error",
                "message": f"Error processing RFP: {str(e)}"
            }

    def handle_rfq_generate(self, text: str = None, message_id: str = None, user_id: str = None) -> Dict:
        """Delegate RFQ draft generation to the dedicated RFQ handler."""
        return self.rfq_handlers.handle_rfq_generate(
            text=text,
            message_id=message_id,
            user_id=user_id,
        )

    

    def handle_generate_quote_with_content(self, opportunity_id: str, content: str, user_id: str = None) -> Dict:
        return self.opportunity_repository.handle_generate_quote_with_content(opportunity_id=opportunity_id, content=content, user_id=user_id)

    def handle_generate_quote_for_opportunity(self, opportunity_id: str, user_id: str = None) -> Dict:
        """Delegate quote generation for an opportunity to the current opportunity backend."""
        return self.opportunity_repository.handle_generate_quote_for_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
        )

    def handle_create_opportunity_manual(self, user_id: str, name: str) -> Dict:
        """Create an opportunity manually via the current opportunity backend."""
        return self.opportunity_repository.create_opportunity_manual(
            user_id=user_id,
            name=name,
        )

    def handle_search_opportunities(
        self,
        user_id: str,
        source_reference_id: str = None,
        name: str = None,
    ) -> Dict:
        """Search opportunities via the current opportunity backend."""
        return self.opportunity_repository.search_opportunities(
            user_id=user_id,
            source_reference_id=source_reference_id,
            name=name,
        )

    def handle_delete_opportunities(self, opportunity_ids: list[str], user_id: str = None) -> Dict:
        """Delete one or more opportunities via the current opportunity backend."""
        return self.opportunity_repository.delete_opportunities(
            opportunity_ids=opportunity_ids,
            user_id=user_id,
        )

    def handle_update_document_content(self, document_id: str, content: str, user_id: str = None) -> Dict:
        """Update the content of a document stored as a text file.
        
        Parameters
        ----------
        document_id : str
            Document ID
        content : str
            New content to save
        user_id : str
            User ID from auth
            
        Returns
        -------
        Dict
            Result with status
        """
        try:
            supabase = get_supabase_service()
            
            # 1. Get document to find storage_key and opportunity_id
            doc_result = supabase.table("document").select("id, storage_key, type, opportunity_id").eq("id", document_id).single().execute()
            if not doc_result.data:
                return {"status": "error", "message": "Document not found"}
            
            document = doc_result.data
            storage_key = document.get("storage_key")
            opportunity_id = document.get("opportunity_id")
            
            if not storage_key:
                return {"status": "error", "message": "Document has no storage file"}
            
            # 2. Get storage directory
            storage_dir = self._get_storage_dir("rfp_upload")
            file_path = storage_dir / storage_key
            
            if not file_path.exists():
                return {"status": "error", "message": f"Document file not found: {storage_key}"}
            
            # 3. Update file content
            file_path.write_text(content, encoding='utf-8')
            print(f"[BusinessHandlers] Updated document content: {document_id} -> {storage_key}")
            
            # 4. Update opportunity's updated_at timestamp
            if opportunity_id:
                try:
                    supabase.table("opportunity").update({"updated_at": datetime.utcnow().isoformat()}).eq("id", opportunity_id).execute()
                    print(f"[BusinessHandlers] Updated opportunity timestamp: {opportunity_id}")
                except Exception as e:
                    print(f"[BusinessHandlers] Warning: Could not update opportunity timestamp: {e}")
            
            return {
                "status": "ok",
                "message": "Document content updated successfully",
                "document_id": document_id
            }
            
        except Exception as e:
            print(f"[BusinessHandlers] Error updating document content: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Failed to update document content: {str(e)}"
            }

    def handle_create_opportunity_from_email(self, message_id: str, user_id: str = None) -> Dict:
        """Create a new_lead opportunity from an email message.
        
        Process:
        1. Classify email to determine category (RFQ, RFP, Quote, etc.)
        2. Extract contact and product info from email
        3. Create or find account based on email sender
        4. Create opportunity record with prefilled data
        """
        try:
            return self.email_handlers.handle_create_opportunity_from_email(message_id, user_id)
        except Exception as e:
            print(f"[BusinessHandlers] Error creating opportunity from email: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error creating opportunity: {str(e)}"
            }
    
    def handle_create_opportunity_from_rfp(self, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_opportunity_from_rfp(
            body=body,
            content_type=content_type,
            user_id=user_id,
        )
    
    @staticmethod
    def _extract_boundary(content_type: str) -> Optional[str]:
        """Extract boundary from Content-Type header.
        
        Parameters
        ----------
        content_type : str
            Content-Type header value
        
        Returns
        -------
        Optional[str]
            Boundary string or None
        """
        if 'boundary=' not in content_type:
            return None
        
        boundary = content_type.split('boundary=')[1]
        # Remove quotes if present
        return boundary.strip('"\'')
    
    @staticmethod
    def _parse_multipart(body: bytes, boundary: str) -> Dict:
        """Parse multipart form data.
        
        Parameters
        ----------
        body : bytes
            Raw multipart body
        boundary : str
            Boundary string
        
        Returns
        -------
        Dict
            Parsed form fields and files
        """
        form_data = {}
        
        # Split by boundary
        parts = body.split(f'--{boundary}'.encode())
        
        for part in parts[1:-1]:  # Skip first empty part and last closing boundary
            if not part.strip():
                continue
            
            # Split headers and content
            try:
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    header_end = part.find(b'\n\n')
                    if header_end == -1:
                        continue
                    content_start = header_end + 2
                else:
                    content_start = header_end + 4
                
                headers = part[:header_end].decode('utf-8', errors='ignore')
                content = part[content_start:]
                
                # Remove trailing CRLF
                if content.endswith(b'\r\n'):
                    content = content[:-2]
                elif content.endswith(b'\n'):
                    content = content[:-1]
                
                # Parse Content-Disposition header
                if 'Content-Disposition' in headers:
                    disp_line = [h for h in headers.split('\n') if 'Content-Disposition' in h][0]
                    
                    # Extract name
                    name_match = 'name="' in disp_line
                    if name_match:
                        name_start = disp_line.find('name="') + 6
                        name_end = disp_line.find('"', name_start)
                        name = disp_line[name_start:name_end]
                        
                        # Check if it's a file (has filename parameter)
                        if 'filename=' in disp_line:
                            filename_start = disp_line.find('filename="') + 10
                            filename_end = disp_line.find('"', filename_start)
                            filename = disp_line[filename_start:filename_end]
                            
                            # Get content type if present
                            content_type = 'application/octet-stream'
                            for header_line in headers.split('\n'):
                                if 'Content-Type:' in header_line:
                                    content_type = header_line.split('Content-Type:')[1].strip()
                            
                            form_data[name] = {
                                'filename': filename,
                                'content': content,
                                'content_type': content_type,
                                'size': len(content)
                            }
                        else:
                            # Text field
                            form_data[name] = content.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"[BusinessHandlers] Error parsing part: {e}")
                continue
        
        return form_data
    
    def _generate_quote_pdf(self, rfp_data: Dict) -> str:
        """Generate PDF from RFP data using HTML template.
        
        Parameters
        ----------
        rfp_data : Dict
            RFP data with products, contact, quote_id, etc.
        
        Returns
        -------
        str
            Filename of generated PDF
        """
        try:
            # Create quotes storage directory if it doesn't exist
            storage_dir = self._get_storage_dir("quote")
            storage_dir.mkdir(parents=True, exist_ok=True)
            templates_dir = Path(__file__).parent.parent.parent / "templates"
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quote_id_num = str(uuid.uuid4())[:8]
            pdf_filename = f"quote_{timestamp}_{quote_id_num}.pdf"
            pdf_path = storage_dir / pdf_filename
            
            # Setup Jinja2 environment
            env = Environment(loader=FileSystemLoader(str(templates_dir)))
            
            # Add custom currency format filter
            def format_currency(value, currency):
                """Format number in French style (space thousands separator, comma decimal)."""
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    return "0,00"
                
                # Currencies with 0 decimal places
                if currency.upper() in ['JPY', 'YEN', 'KRW', 'CNY', 'RUB']:
                    decimals = 0
                # Currencies with 3 decimal places
                elif currency.upper() in ['BHD', 'JOD', 'KWD', 'OMR', 'TND']:
                    decimals = 3
                # Default to 2 decimal places
                else:
                    decimals = 2
                
                # Format with US style first (comma thousands, dot decimal)
                formatted = f"{value:,.{decimals}f}"
                
                # Convert to French style: replace comma with space for thousands, dot with comma for decimals
                # "1,234.56" becomes "1 234,56"
                parts = formatted.split('.')
                integer_part = parts[0].replace(',', ' ')
                decimal_part = parts[1] if len(parts) > 1 else ''
                
                if decimal_part:
                    return f"{integer_part},{decimal_part}"
                else:
                    return integer_part
            
            env.filters['format_currency'] = format_currency
            template = env.get_template('quote.html')
            
            # Prepare template data
            template_data = {
                'quote_id': rfp_data.get('quote_id', f"QT-{quote_id_num}"),
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'issued_date': rfp_data.get('issued_date', ''),
                'valid_until': rfp_data.get('valid_until', ''),
                'title': rfp_data.get('title', ''),
                'contact': rfp_data.get('contact', {}),
                'account': rfp_data.get('account', {}),
                'products': [],
                'currency': rfp_data.get('currency', 'EUR'),
                'totals': rfp_data.get('totals', {}),

            }
            
            # Format products for template
            for product in rfp_data.get('products', []):
                try:
                    quantity = float(product.get('quantity', 1) or 1)
                except Exception:
                    quantity = 1.0

                try:
                    unit_price_excl_tax = float(product.get('unit_price_excl_tax', product.get('price', 0)) or 0)
                except Exception:
                    unit_price_excl_tax = 0.0

                try:
                    client_discount_rate = float(product.get('client_discount_rate', 0) or 0)
                except Exception:
                    client_discount_rate = 0.0

                discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)

                try:
                    line_total_excl_tax = float(product.get('line_total_excl_tax'))
                except Exception:
                    line_total_excl_tax = quantity * discounted_unit_price

                template_data['products'].append({
                    'quantity': quantity,
                    'brand': product.get('brand', '') or product.get('manufacturer', ''),
                    'manufacturer': product.get('manufacturer', ''),
                    'sku': product.get('sku', ''),
                    'description': product.get('description', ''),
                    'price': unit_price_excl_tax,
                    'unit_price_excl_tax': unit_price_excl_tax,
                    'discounted_unit_price': discounted_unit_price,
                    'client_discount_rate': client_discount_rate,
                    'line_total_excl_tax': line_total_excl_tax,
                    'selling_price': product.get('selling_price'),
                    'price_found': unit_price_excl_tax > 0,
                })
            
            # Render HTML
            html_content = template.render(**template_data)
            
            # Generate PDF from HTML using WeasyPrint
            HTML(string=html_content).write_pdf(str(pdf_path))
            
            print(f"[BusinessHandlers] PDF saved to {pdf_path}")
            return pdf_filename
            
        except Exception as e:
            print(f"[BusinessHandlers] Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            raise

    
    def handle_generate_quote_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate a PDF for an existing quote document and update storage_key."""
        supabase = get_supabase_service()

        try:
            # Load document with opportunity
            doc_resp = supabase.table("document").select("*").eq("id", document_id).single().execute()
            if getattr(doc_resp, "error", None):
                return {"status": "error", "message": f"Document lookup failed: {doc_resp.error}"}
            document = doc_resp.data
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "PDF generation is only supported for quotes"}

            # Load opportunity and account
            opportunity_id = document.get("opportunity_id")
            account_id = None
            opportunity = {}
            account = {}
            
            if opportunity_id:
                opp_resp = supabase.table("opportunity").select("*").eq("id", opportunity_id).single().execute()
                if not getattr(opp_resp, "error", None) and opp_resp.data:
                    opportunity = opp_resp.data
                    account_id = opportunity.get("account_id")
                    
                    if account_id:
                        acc_resp = supabase.table("account").select("*").eq("id", account_id).single().execute()
                        if not getattr(acc_resp, "error", None) and acc_resp.data:
                            account = acc_resp.data
                            print(f"[BusinessHandlers] Loaded account: {account}")
                    else:
                        print(f"[BusinessHandlers] No account_id in opportunity {opportunity_id}")
                else:
                    print(f"[BusinessHandlers] Could not load opportunity {opportunity_id}")

            # Load lines
            line_resp = supabase.table("document_line").select("*").eq("document_id", document_id).order("position").execute()
            if getattr(line_resp, "error", None):
                return {"status": "error", "message": f"Document lines lookup failed: {line_resp.error}"}
            lines = line_resp.data or []

            def _select_best_family_for_sku(product: Dict, direct_net_price_family: Dict | None):
                if isinstance(direct_net_price_family, dict):
                    if str(direct_net_price_family.get("type") or "").lower() == "net_price":
                        return direct_net_price_family

                links = product.get("product_family") or []
                if not isinstance(links, list):
                    return None

                best_discount_family = None
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

            def _compute_quote_unit_price(line: Dict, product: Dict, best_family: Dict | None) -> float:
                try:
                    list_price = float((product or {}).get("price") or 0)
                except Exception:
                    list_price = 0.0

                family_type = str((best_family or {}).get("type") or "").lower()
                if family_type == "net_price":
                    purchased_price = float((best_family or {}).get("net_price") or 0)
                else:
                    family_discount = float((best_family or {}).get("discount") or 0)
                    purchased_price = list_price * (1 - family_discount / 100.0)

                has_effective_family_pricing = False
                if family_type == "net_price":
                    has_effective_family_pricing = (best_family or {}).get("net_price") is not None
                elif family_type == "discount":
                    has_effective_family_pricing = float((best_family or {}).get("discount") or 0) > 0

                brand = (product or {}).get("brand") if isinstance((product or {}).get("brand"), dict) else {}
                client_discount_rate = float((line or {}).get("client_discount_rate") or 0)
                client_discount_factor = 1 - client_discount_rate / 100.0

                if not has_effective_family_pricing:
                    return list_price * client_discount_factor

                return list_price * client_discount_factor

            # Build pricing fallbacks for lines that were persisted with zero prices.
            fallback_by_sku: Dict[str, Dict] = {}
            skus_needing_fallback = list({
                str((line or {}).get("sku") or "").strip()
                for line in lines
                if str((line or {}).get("sku") or "").strip()
                and (
                    float((line or {}).get("unit_price_excl_tax") or 0) <= 0
                    or float((line or {}).get("line_total_excl_tax") or 0) <= 0
                )
            })

            if skus_needing_fallback:
                product_resp = (
                    supabase.table("product")
                    .select("sku, price, brand(*), product_family(family(*))")
                    .in_("sku", skus_needing_fallback)
                    .execute()
                )
                product_by_sku = {
                    str((p or {}).get("sku") or "").strip(): p
                    for p in (product_resp.data or [])
                    if str((p or {}).get("sku") or "").strip()
                }

                net_price_resp = (
                    supabase.table("family")
                    .select("*")
                    .in_("product_code", skus_needing_fallback)
                    .ilike("type", "net_price")
                    .execute()
                )
                net_price_family_by_sku = {
                    str((f or {}).get("product_code") or "").strip(): f
                    for f in (net_price_resp.data or [])
                    if str((f or {}).get("product_code") or "").strip()
                }

                for sku in skus_needing_fallback:
                    product = product_by_sku.get(sku)
                    if not isinstance(product, dict):
                        continue
                    best_family = _select_best_family_for_sku(product, net_price_family_by_sku.get(sku))
                    fallback_by_sku[sku] = {
                        "unit_price_excl_tax": _compute_quote_unit_price({"client_discount_rate": 0}, product, best_family),
                        "best_family": best_family,
                    }

            # Build rfp-like structure for PDF generator
            rfp_data = {
                "quote_id": document.get("id"),
                "title": document.get("title") or "Quote",
                "products": [],
                "contact": {
                    "company_name": account.get("name", ""),
                    "address": self._normalize_account_address(account),
                },
                "account": account,
                "issued_date": document.get("issued_at") or datetime.now().isoformat(),
                "valid_until": document.get("valid_until"),
                "currency": document.get("currency", "EUR"),
                "totals": {
                    "subtotal": 0.0,
                    "tax": 0.0,
                    "total": 0.0,
                },
            }

            computed_subtotal = 0.0
            computed_tax = 0.0

            for line in lines:
                sku = str(line.get("sku") or "").strip()
                try:
                    quantity = float(line.get("quantity", 1) or 1)
                except Exception:
                    quantity = 1.0

                try:
                    unit_price_excl_tax = float(line.get("unit_price_excl_tax", 0) or 0)
                except Exception:
                    unit_price_excl_tax = 0.0

                if unit_price_excl_tax <= 0 and sku in fallback_by_sku:
                    # Use recomputed quote price when persisted line price is missing.
                    unit_price_excl_tax = float((fallback_by_sku.get(sku) or {}).get("unit_price_excl_tax") or 0)

                try:
                    client_discount_rate = float(line.get("client_discount_rate", 0) or 0)
                except Exception:
                    client_discount_rate = 0.0

                discounted_unit_price = unit_price_excl_tax * (1 - client_discount_rate / 100.0)

                try:
                    line_total_excl_tax = float(line.get("line_total_excl_tax", 0) or 0)
                except Exception:
                    line_total_excl_tax = 0.0

                if line_total_excl_tax <= 0:
                    line_total_excl_tax = quantity * discounted_unit_price

                try:
                    tax_rate = float(line.get("tax_rate", 20) or 20)
                except Exception:
                    tax_rate = 20.0

                computed_subtotal += line_total_excl_tax
                computed_tax += line_total_excl_tax * (tax_rate / 100.0)

                rfp_data["products"].append({
                    "quantity": quantity,
                    "brand": line.get("brand", ""),
                    "manufacturer": line.get("brand", ""),
                    "sku": line.get("sku"),
                    "description": line.get("description"),
                    "price": unit_price_excl_tax,
                    "unit_price_excl_tax": unit_price_excl_tax,
                    "client_discount_rate": client_discount_rate,
                    "discounted_unit_price": discounted_unit_price,
                    "line_total_excl_tax": line_total_excl_tax,
                    "tax_rate": tax_rate,
                    "unit": line.get("unit", "U"),
                })

            computed_subtotal = round(computed_subtotal, 2)
            computed_tax = round(computed_tax, 2)
            computed_total = round(computed_subtotal + computed_tax, 2)
            rfp_data["totals"] = {
                "subtotal": computed_subtotal,
                "tax": computed_tax,
                "total": computed_total,
            }

            pdf_filename = self._generate_quote_pdf(rfp_data)

            update_payload = {
                "storage_key": pdf_filename,
                "total_excl_tax": computed_subtotal,
                "total_tax": computed_tax,
                "total_incl_tax": computed_total,
            }

            upd_resp = supabase.table("document").update(update_payload).eq("id", document_id).execute()
            if getattr(upd_resp, "error", None):
                # Backward compatibility: allow PDF generation even if totals columns
                # are not yet available in a given environment.
                print(f"[BusinessHandlers] Warning updating totals on document {document_id}: {upd_resp.error}")
                fallback_resp = (
                    supabase.table("document")
                    .update({"storage_key": pdf_filename})
                    .eq("id", document_id)
                    .execute()
                )
                if getattr(fallback_resp, "error", None):
                    return {
                        "status": "error",
                        "message": f"Failed to update document with PDF: {fallback_resp.error}",
                    }

            return {
                "status": "ok",
                "pdf_filename": pdf_filename,
            }

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error generating PDF for document {document_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error generating PDF: {str(e)}",
            }

    def update_line_from_product(self, document: Dict, product: Dict) -> None:
        print(f"[BusinessHandlers][update_line_from_product] Updating line from product: {product}")

        response = self.supabase.table("document_line").select("*").eq("id", product.get("id")).single().execute()
        if not response.data:
            line = {
                "document_id": document.get("id"),
            }
        else:
            line = response.data
        line['description'] = product.get("description")
        line['position'] = product.get("position")
        line["sku"] = product.get("sku")
        line['quantity'] = product.get("quantity")
        line['unit'] = product.get("unit")
        line['unit_price'] = product.get("price")
        line['unit_price_excl_tax'] = product.get("price")
        line['tax_rate'] = product.get("tax_rate", 20)
        line['discount_rate'] = product.get("discount_rate", 0)
        line['line_total_excl_tax'] = round(float(product.get("quantity", 1) or 1) * float(product.get("price", 0) or 0), 2)
        

    def handle_update_entity_field(self, table: str, field: str, record_id: str, value, user_id: str = None) -> Dict:
        """Update a single field on a table by record id.

        Expects a valid table and field name, and updates by primary key "id".
        """
        

        try:
            if not table or not field:
                return {"status": "error", "message": "Missing table or field"}

            name_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
            if not name_re.match(table) or not name_re.match(field):
                return {"status": "error", "message": "Invalid table or field"}

            if not record_id:
                return {"status": "error", "message": "Missing id"}

            update_resp = (
                self.supabase.table(table)
                .update({field: value})
                .eq("id", record_id)
                .execute()
            )

            if getattr(update_resp, "error", None):
                return {"status": "error", "message": f"Failed to update: {update_resp.error}"}

            if not update_resp.data:
                return {"status": "error", "message": "No rows updated"}

            return {"status": "ok", "data": update_resp.data[0]}

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error in handle_update_entity_field: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def handle_delete_quote_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete a quote document and its related data.
        
        Parameters
        ----------
        document_id : str
            Document UUID
        user_id : str, optional
            User ID (for authorization)
        
        Returns
        -------
        Dict
            Response with status and details
        """
        try:
            supabase = get_supabase_service()

            # Verify document exists and belongs to user
            doc_resp = supabase.table("document").select("id, type, storage_key, opportunity_id").eq("id", document_id).maybe_single().execute()
            document = doc_resp.data if doc_resp and doc_resp.data else None

            if not document:
                return {"status": "error", "message": "Quote document not found"}

            if document.get("type") != "QUOTE":
                return {"status": "error", "message": "Document is not a quote"}

            # Delete PDF file if exists
            if document.get("storage_key"):
                try:
                    # Try storage directories first
                    storage_path = self._get_storage_path("quote", document.get("storage_key"))
                    if storage_path.exists():
                        storage_path.unlink()
                        print(f"[BusinessHandlers] Deleted PDF file: {storage_path}")
                    else:
                        # Fallback to legacy assets directory
                        assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                        pdf_path = assets_dir / document.get("storage_key")
                        if pdf_path.exists():
                            pdf_path.unlink()
                            print(f"[BusinessHandlers] Deleted PDF file: {pdf_path}")
                except Exception as e:
                    print(f"[BusinessHandlers] Warning: Could not delete PDF file: {e}")

            # Delete document (cascade will delete document_line and quote entries)
            delete_resp = supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete quote: {delete_resp.error}"}

            return {
                "status": "ok",
                "message": "Quote deleted successfully",
            }

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error deleting quote document {document_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error deleting quote: {str(e)}",
            }

    def handle_delete_document(self, document_id: str, user_id: str = None) -> Dict:
        """Delete any document and its related data (generic handler for all document types).
        
        Parameters
        ----------
        document_id : str
            Document UUID
        user_id : str, optional
            User ID (for authorization)
        
        Returns
        -------
        Dict
            Response with status and details
        """
        try:
            supabase = get_supabase_service()

            # Verify document exists
            doc_resp = supabase.table("document").select("id, type, storage_key, opportunity_id").eq("id", document_id).maybe_single().execute()
            document = doc_resp.data if doc_resp and doc_resp.data else None

            if not document:
                return {"status": "error", "message": "Document not found"}

            doc_type = document.get("type", "").lower()

            # Delete PDF/file if exists
            if document.get("storage_key"):
                try:
                    # Determine storage directory based on document type
                    storage_type = "quote" if doc_type == "quote" else "invoice" if doc_type == "invoice" else "rfp_upload"
                    storage_path = self._get_storage_path(storage_type, document.get("storage_key"))
                    
                    if storage_path.exists():
                        storage_path.unlink()
                        print(f"[BusinessHandlers] Deleted file: {storage_path}")
                    else:
                        # Fallback to legacy assets directory
                        assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                        file_path = assets_dir / document.get("storage_key")
                        if file_path.exists():
                            file_path.unlink()
                            print(f"[BusinessHandlers] Deleted file: {file_path}")
                except Exception as e:
                    print(f"[BusinessHandlers] Warning: Could not delete file: {e}")

            # Delete document (cascade will delete document_line entries)
            delete_resp = supabase.table("document").delete().eq("id", document_id).execute()
            if getattr(delete_resp, "error", None):
                return {"status": "error", "message": f"Failed to delete document: {delete_resp.error}"}

            return {
                "status": "ok",
                "message": f"{document.get('type', 'Document')} deleted successfully",
            }

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error deleting document {document_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error deleting document: {str(e)}",
            }
    
    def handle_list_quotes(self) -> Dict:
        """List all generated quotes.
        
        Returns
        -------
        Dict
            List of available quote files
        """
        try:
            assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all PDF files
            pdf_files = sorted(
                [f.name for f in assets_dir.glob('quote_*.pdf')],
                reverse=True
            )
            
            return {
                "status": "ok",
                "quotes": pdf_files,
                "total": len(pdf_files)
            }
        except Exception as e:
            print(f"[BusinessHandlers] Error listing quotes: {e}")
            return {
                "status": "error",
                "message": f"Error listing quotes: {str(e)}"
            }
    
    def handle_get_quote_file(self, filename: str) -> bytes:
        """Retrieve a quote PDF file.
        
        Parameters
        ----------
        filename : str
            PDF filename
        
        Returns
        -------
        bytes
            PDF file content
        
        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        """
        try:
            # Validate filename format to prevent path traversal
            if not filename.startswith('quote_') or not filename.endswith('.pdf'):
                raise ValueError(f"Invalid filename format: {filename}")
            
            # Primary check: new organized storage structure
            pdf_path = self._get_storage_path("quote", filename)
            
            if not pdf_path.exists():
                # Fallback: check old /var/assets location for legacy PDFs
                legacy_assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                legacy_pdf_path = legacy_assets_dir / filename
                
                if legacy_pdf_path.exists():
                    pdf_path = legacy_pdf_path
                else:
                    raise FileNotFoundError(f"Quote file not found: {filename}")
            
            return pdf_path.read_bytes()
        except FileNotFoundError:
            raise
        except Exception as e:
            print(f"[BusinessHandlers] Error retrieving quote: {e}")
            raise FileNotFoundError(f"Error retrieving quote: {str(e)}")
    
    def handle_quote_send(self, body: bytes, content_type: str) -> Dict:
        """Delegate quote send flow to EmailHandlers."""
        return self.email_handlers.handle_quote_send(body, content_type)

    def handle_send_quote_for_opportunity(self, opportunity_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Delegate quote send for an opportunity to EmailHandlers."""
        return self.email_handlers.handle_send_quote_for_opportunity(
            opportunity_id=opportunity_id,
            payload=payload,
            user_id=user_id,
        )

    @staticmethod
    def _get_storage_dir(source: str) -> Path:
        """Get storage directory path based on source type.
        
        Parameters
        ----------
        source : str
            Source type (e.g., 'rfp_upload', 'email', 'quote', etc.)
        
        Returns
        -------
        Path
            Storage directory for the source type
        """
        base_storage = Path("var/storage")
        
        # Map source types to storage subdirectories
        source_map = {
            "rfp_upload": "rfp_uploads",
            "email": "emails",
            "quote": "quotes",
            "invoice": "invoices",
            "attachment": "attachments"
        }
        
        subdir = source_map.get(source, source)
        storage_dir = base_storage / subdir
        
        return storage_dir
    
    @staticmethod
    def _get_storage_path(source: str, filename: str) -> Path:
        """Get full file path in storage based on source type and filename.
        
        Parameters
        ----------
        source : str
            Source type (e.g., 'rfp_upload', 'email', etc.)
        filename : str
            Filename within the storage directory
        
        Returns
        -------
        Path
            Full file path
        """
        storage_dir = BusinessHandlers._get_storage_dir(source)
        return storage_dir / filename

    def handle_extract_rfp_from_document(self, document_id: str, user_id: str = None) -> Dict:
        """Extract RFP data from a document (PDF or text file).
        
        Process:
        1. Get document from database
        2. Read file from storage
        3. Extract text (PDF or plain text)
        4. Extract RFP data using LLM
        5. Return extracted products and contact info
        
        Parameters
        ----------
        document_id : str
            Document ID to extract from
        user_id : str
            User ID from auth
        
        Returns
        -------
        Dict
            Result with extracted RFP data
        """
        try:
            supabase = get_supabase_service()
            
            # Get document from database
            doc_result = supabase.table("document").select("*").eq("id", document_id).single().execute()
            if not doc_result.data:
                return {"status": "error", "message": "Document not found"}
            
            document = doc_result.data
            storage_key = document.get("storage_key")
            
            if not storage_key:
                return {"status": "error", "message": "Document has no storage key"}
            
            # Read file from storage
            file_path = self._get_storage_path("rfp_upload", storage_key)
            
            if not file_path.exists():
                return {"status": "error", "message": "Document file not found in storage"}
            
            # Extract text based on file type
            file_ext = file_path.suffix.lower()
            
            if file_ext == ".pdf":
                # Extract text from PDF
                try:
                    from src.pdf.extract_text import extract_text
                    content = extract_text(file_path)
                    if not content:
                        return {"status": "error", "message": "Could not extract text from PDF"}
                except Exception as e:
                    print(f"[BusinessHandlers] Error extracting PDF: {e}")
                    return {"status": "error", "message": f"Failed to extract PDF: {str(e)}"}
            else:
                # Plain text file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"[BusinessHandlers] Error reading text file: {e}")
                    return {"status": "error", "message": f"Failed to read file: {str(e)}"}
            
            if not content or not content.strip():
                return {"status": "error", "message": "Document is empty"}
            
            # Clean content
            message_clean = self._clean_email_body(content)
            
            # Extract RFP data
            try:
                rfp_data = extract_rfp_from_text(message_clean)
                if not isinstance(rfp_data, dict):
                    rfp_data = {"products": [], "contact": {}}
                
                # Extract contact/company information
                try:
                    company_data = extract_company_from_text(message_clean)
                    if isinstance(company_data, dict) and company_data:
                        rfp_data["contact"] = company_data
                        print(f"[BusinessHandlers] Extracted company data from document: {company_data}")
                except Exception as e:
                    print(f"[BusinessHandlers] Warning: Failed to extract company data: {e}")
                
                # Normalize extracted pricing fields (same helper used by quote generation)
                rfp_data = self.opportunity_repository._extract_and_enrich_rfp_data(
                    message_clean,
                    pre_extracted_data=rfp_data
                )
                
                print(f"[BusinessHandlers] Extracted and enriched RFP data from document {document_id}")
                
                return {
                    "status": "ok",
                    "data": rfp_data,
                    "document_id": document_id
                }
                
            except Exception as e:
                print(f"[BusinessHandlers] Error extracting RFP: {e}")
                return {"status": "error", "message": f"Failed to extract RFP data: {str(e)}"}
            
        except Exception as e:
            print(f"[BusinessHandlers] Error in handle_extract_rfp_from_document: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def handle_create_rfq_source_from_html_body(self, opportunity_id: str, body: bytes, content_type: str, user_id: str = None) -> Dict:
        return self.rfq_handlers.handle_create_rfq_source_from_html_body(
            opportunity_id=opportunity_id,
            body=body,
            content_type=content_type,
            user_id=user_id,
        )

    def handle_chat_attachment_upload(self, body: bytes, content_type: str, user_id: str, opportunity_id: str) -> Dict:
        """Handle chat attachment upload: store file and create document record."""
        if not user_id:
            return {"status": "error", "message": "Missing user_id"}
        if not opportunity_id:
            return {"status": "error", "message": "Missing opportunity_id"}

        form_data, error = self.getForm(body, content_type)
        if error:
            return error
        uploaded_file = form_data.get('file')
        if not uploaded_file or not isinstance(uploaded_file, dict):
            return {"status": "error", "message": "No file provided"}

        filename = uploaded_file.get('filename')
        file_content = uploaded_file.get('content')
        mime_type = uploaded_file.get('content_type')
        file_size = uploaded_file.get('size')

        if not filename or not file_content:
            return {"status": "error", "message": "Invalid file payload"}

        supabase = get_supabase_service()

        try:
            base_dir = Path(__file__).resolve().parents[2] / "var" / "attachments" / user_id / "chat" / str(uuid.uuid4())
            base_dir.mkdir(parents=True, exist_ok=True)

            unique_name = f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"
            file_path = base_dir / unique_name
            file_path.write_bytes(file_content)

            storage_key = unique_name

            storage_dir = self._get_storage_dir("attachment")
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

            doc_result = supabase.table("document").insert(doc_data).execute()
            if not doc_result.data:
                return {"status": "error", "message": "Failed to create document"}

            document_id = doc_result.data[0]["id"]

            try:
                supabase.table("opportunity").update({"updated_at": datetime.now().isoformat()}).eq(
                    "id", opportunity_id
                ).execute()
            except Exception as e:
                print(f"[BusinessHandlers] Warning: failed to touch opportunity {opportunity_id}: {e}")

            return {
                "status": "ok",
                "document_id": document_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": file_size,
                "storage_key": storage_key,
            }
        except Exception as e:
            print(f"[BusinessHandlers] Error uploading chat attachment: {e}")
            return {"status": "error", "message": f"Upload failed: {str(e)}"}
        

    def handle_update_line_verification(self, document_id: str, line_index: int, verification_fields: dict = None, is_ref_verified: bool = None, user_id: str = None) -> Dict:
        """Update verification status for a specific line in a quote document.
        
        Args:
            document_id: ID of the quote document
            line_index: Position/index of the line (1-based)
            verification_fields: Dict of verification fields to update (e.g., {'is_ref_verified': True, 'is_quantity_verified': False})
            is_ref_verified: (Deprecated) Single field for backward compatibility
            user_id: ID of the user making the change
        
        Returns:
            {"status": "ok"} or {"status": "error", "message": "..."}
        """
        supabase = get_supabase_service()
        
        try:
            # Support both old and new interfaces
            if verification_fields is None:
                verification_fields = {}
                if is_ref_verified is not None:
                    verification_fields['is_ref_verified'] = is_ref_verified
            
            if not verification_fields:
                return {"status": "error", "message": "No verification fields provided"}
            
            print(f"[BusinessHandlers] Starting line verification update: doc={document_id}, line={line_index}, fields={verification_fields}")
            
            # Verify document exists
            doc_resp = supabase.table("document").select("id").eq("id", document_id).single().execute()
            if getattr(doc_resp, "error", None):
                error_msg = f"Document lookup failed: {doc_resp.error}"
                print(f"[BusinessHandlers] {error_msg}")
                return {"status": "error", "message": error_msg}
            
            document = doc_resp.data
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}
            
            print(f"[BusinessHandlers] Found document: {document_id}")
            
            # First, check if the document_line exists
            print(f"[BusinessHandlers] Checking if document_line exists: document_id={document_id}, position={line_index}")
            check_resp = supabase.table("document_line").select("id, position, document_id").eq("document_id", document_id).eq("position", line_index).execute()
            
            print(f"[BusinessHandlers] Check response: {check_resp.data}")
            if not check_resp.data or len(check_resp.data) == 0:
                print(f"[BusinessHandlers] WARNING: No document_line found for doc={document_id}, position={line_index}")
                # Try to fetch all lines for this document to debug
                all_lines_resp = supabase.table("document_line").select("position, document_id").eq("document_id", document_id).execute()
                print(f"[BusinessHandlers] All lines for this document: {all_lines_resp.data}")
            
            # Update the specific line by document_id and position with all provided fields
            print(f"[BusinessHandlers] Updating document_line where document_id={document_id} and position={line_index} with fields: {verification_fields}")
            upd_resp = supabase.table("document_line").update(verification_fields).eq("document_id", document_id).eq("position", line_index).execute()
            
            print(f"[BusinessHandlers] Update response: {upd_resp}")
            print(f"[BusinessHandlers] Update response error: {getattr(upd_resp, 'error', None)}")
            print(f"[BusinessHandlers] Update response count: {getattr(upd_resp, 'count', None)}")
            print(f"[BusinessHandlers] Update response data type: {type(upd_resp.data)}")
            print(f"[BusinessHandlers] Update response data: {upd_resp.data}")
            if upd_resp.data:
                print(f"[BusinessHandlers] Number of rows updated: {len(upd_resp.data)}")
            else:
                print(f"[BusinessHandlers] WARNING: No rows updated (upd_resp.data is empty or None)")
            
            if getattr(upd_resp, "error", None):
                error_msg = str(upd_resp.error)
                print(f"[BusinessHandlers] Update error: {error_msg}")
                
                # Check if error is about schema cache not being updated
                if "Could not find the" in error_msg or "PGRST204" in error_msg:
                    print(f"[BusinessHandlers] Schema cache error - Supabase needs to refresh. Retrying...")
                    # Supabase schema cache might not be updated yet
                    # Try using raw SQL through the query builder
                    import time
                    time.sleep(1)  # Wait a moment
                    
                    # Try again with a slightly different approach
                    upd_resp = supabase.table("document_line").update(verification_fields).eq("document_id", document_id).eq("position", line_index).execute()
                    
                    if getattr(upd_resp, "error", None):
                        return {"status": "error", "message": f"Failed to update line: {upd_resp.error}"}
                else:
                    return {"status": "error", "message": f"Failed to update line: {error_msg}"}
            
            print(f"[BusinessHandlers] Update response data: {upd_resp.data}")
            print(f"[BusinessHandlers] Updated line verification: doc={document_id}, line={line_index}, fields={verification_fields}")
            
            # Verify the update was actually persisted by reading it back
            print(f"[BusinessHandlers] VERIFYING: Reading back the updated record from database...")
            verify_resp = supabase.table("document_line").select("*").eq("document_id", document_id).eq("position", line_index).execute()
            print(f"[BusinessHandlers] VERIFICATION READ: {verify_resp.data}")
            
            if getattr(verify_resp, "error", None):
                error_msg = str(verify_resp.error)
                print(f"[BusinessHandlers] VERIFICATION ERROR: {error_msg}")
                return {"status": "error", "message": f"Failed to verify update: {error_msg}"}
            
            if verify_resp.data and len(verify_resp.data) > 0:
                record = verify_resp.data[0]
                all_match = True
                for field_name, field_value in verification_fields.items():
                    db_value = record.get(field_name)
                    match = field_value == db_value
                    print(f"[BusinessHandlers] VERIFY {field_name}: sent={field_value}, database has={db_value}, match={match}")
                    if not match:
                        all_match = False
                
                if not all_match:
                    return {"status": "error", "message": f"Update failed: values not persisted in database"}
            else:
                return {"status": "error", "message": f"Update failed: record not found after update"}
            
            return {"status": "ok"}
            
        except Exception as e:
            print(f"[BusinessHandlers] Error in handle_update_line_verification: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def handle_get_document_file(self, filename: str) -> bytes:
        """Retrieve a document file (PDF, DOCX, etc.) from storage or assets directory.
        
        Parameters
        ----------
        filename : str
            Document filename (can include subdirectories)
        
        Returns
        -------
        bytes
            Document file content
        
        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        ValueError
            If filename is invalid (path traversal attempt)
        """
        try:
            # Prevent path traversal attacks
            if '..' in filename or filename.startswith('/'):
                raise ValueError(f"Invalid filename format: {filename}")
            
            file_path = None
            
            # Check storage directories first (quotes, invoices, attachments, etc.)
            storage_subdirs = ['rfp_uploads', 'attachment', 'attachments', 'email', 'quotes', 'invoices']
            for subdir in storage_subdirs:
                candidate = Path(__file__).parent.parent.parent / "var" / "storage" / subdir / filename
                if candidate.exists():
                    file_path = candidate
                    break
            
            # Fallback to assets directory for other files or legacy PDFs
            if not file_path or not file_path.exists():
                assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                assets_file = assets_dir / filename
                
                # Additional safety check - ensure file is within assets_dir
                if str(assets_file.resolve()).startswith(str(assets_dir.resolve())):
                    if assets_file.exists():
                        file_path = assets_file
            
            if not file_path or not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {filename}")
            
            return file_path.read_bytes()
        except FileNotFoundError:
            raise
        except Exception as e:
            print(f"[BusinessHandlers] Error retrieving document: {e}")
            raise

    def handle_generate_invoice_from_quote(self, quote_id: str, user_id: str = None) -> Dict:
        """Generate an INVOICE document from an accepted QUOTE.
        
        The invoice is created as a separate document with the quote as parent_document_id.
        quote_id can be either a document ID or an opportunity ID. If it's an opportunity ID,
        we'll fetch the latest QUOTE document for that opportunity.
        """
        supabase = get_supabase_service()

        try:
            # First, try to fetch as document ID
            quote_resp = supabase.table("document").select("*").eq("id", quote_id).execute()
            
            # If no document found, try as opportunity ID to find the quote
            if not quote_resp.data or len(quote_resp.data) == 0:
                quote_resp = supabase.table("document").select("*").eq("opportunity_id", quote_id).eq("type", "QUOTE").order("created_at", desc=True).limit(1).execute()
            
            if getattr(quote_resp, "error", None) or not quote_resp.data:
                return {"status": "error", "message": f"Quote not found for {quote_id}"}
            
            quote = quote_resp.data[0]

            if quote.get("type") != "QUOTE":
                return {"status": "error", "message": "Document must be a QUOTE"}

            quote_id = quote.get("id")  # Use the actual quote document ID
            
            # Check if invoice already exists for this quote
            existing_resp = supabase.table("document").select("id").eq("parent_document_id", quote_id).eq("type", "INVOICE").execute()
            if existing_resp.data and len(existing_resp.data) > 0:
                return {"status": "error", "message": "Invoice already exists for this quote"}

            # Load quote lines
            line_resp = supabase.table("document_line").select("*").eq("document_id", quote_id).order("position").execute()
            if getattr(line_resp, "error", None):
                return {"status": "error", "message": f"Failed to load quote lines: {line_resp.error}"}
            lines = line_resp.data or []

            # Create invoice document
            invoice_data = {
                "type": "INVOICE",
                "status": "DRAFT",
                "opportunity_id": quote.get("opportunity_id"),
                "parent_document_id": quote_id,
                "title": f"Invoice - {quote.get('title', 'Quote')}",
                "external_ref": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "currency": quote.get("currency", "EUR"),
                "total_excl_tax": quote.get("total_excl_tax", 0),
                "total_tax": quote.get("total_tax", 0),
                "total_incl_tax": quote.get("total_incl_tax", 0),
                "issued_at": datetime.now().isoformat(),
            }

            inv_resp = supabase.table("document").insert([invoice_data]).execute()
            if getattr(inv_resp, "error", None) or not inv_resp.data:
                return {"status": "error", "message": f"Failed to create invoice: {inv_resp.error}"}
            
            invoice_id = inv_resp.data[0]["id"]

            # Copy lines from quote to invoice
            invoice_lines = []
            for line in lines:
                invoice_lines.append({
                    "document_id": invoice_id,
                    "position": line.get("position"),
                    "sku": line.get("sku"),
                    "brand": line.get("brand"),
                    "description": line.get("description"),
                    "quantity": line.get("quantity"),
                    "unit": line.get("unit"),
                    "unit_price_excl_tax": line.get("unit_price_excl_tax"),
                    "tax_rate": line.get("tax_rate"),
                    "line_total_excl_tax": line.get("line_total_excl_tax"),
                })

            if invoice_lines:
                line_insert_resp = supabase.table("document_line").insert(invoice_lines).execute()
                if getattr(line_insert_resp, "error", None):
                    return {"status": "error", "message": f"Failed to copy lines to invoice: {line_insert_resp.error}"}

            print(f"[BusinessHandlers] Invoice {invoice_id} created from quote {quote_id}")

            # Automatically generate PDF for the invoice
            storage_key = None
            try:
                pdf_result = self.handle_generate_invoice_pdf(document_id=invoice_id, user_id=user_id)
                if pdf_result.get("status") == "ok":
                    storage_key = pdf_result.get("storage_key")
                    print(f"[BusinessHandlers] Invoice PDF generated automatically: {storage_key}")
                else:
                    print(f"[BusinessHandlers] Warning: Could not auto-generate invoice PDF: {pdf_result.get('message')}")
            except Exception as pdf_error:
                print(f"[BusinessHandlers] Warning: Error auto-generating invoice PDF: {pdf_error}")

            return {
                "status": "ok",
                "invoice_id": invoice_id,
                "invoice": {
                    "id": invoice_id,
                    "title": invoice_data["title"],
                    "external_ref": invoice_data["external_ref"],
                    "currency": invoice_data["currency"],
                    "storage_key": storage_key,
                    "totals": {
                        "subtotal": invoice_data["total_excl_tax"],
                        "tax": invoice_data["total_tax"],
                        "total": invoice_data["total_incl_tax"],
                    },
                },
            }

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error generating invoice from quote {quote_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error generating invoice: {str(e)}",
            }

    def handle_send_invoice(self, invoice_id: str, payload: Dict, user_id: str = None) -> Dict:
        """Send invoice email with PDF attachment.
        
        Parameters
        ----------
        invoice_id : str
            The invoice document UUID
        payload : Dict
            Email data: {to: [emails], cc: [emails], subject, body}
        user_id : str, optional
            User ID for authorization
        
        Returns
        -------
        Dict
            Response with status and message
        """
        try:
            supabase = get_supabase_service()
            
            # Load invoice document
            invoice_resp = supabase.table("document").select("*").eq("id", invoice_id).single().execute()
            if getattr(invoice_resp, "error", None) or not invoice_resp.data:
                return {"status": "error", "message": "Invoice not found"}
            
            invoice = invoice_resp.data
            
            if invoice.get("type") != "INVOICE":
                return {"status": "error", "message": "Document is not an invoice"}
            
            storage_key = invoice.get("storage_key")
            if not storage_key:
                return {"status": "error", "message": "Invoice PDF not generated yet"}
            
            # Validate required fields
            to_emails = payload.get('to', [])
            cc_emails = payload.get('cc', [])
            subject = payload.get('subject', f"Invoice {invoice.get('external_ref', '')}")
            body = payload.get('body', 'Please find attached your invoice.')
            
            if not to_emails or not isinstance(to_emails, list) or len(to_emails) == 0:
                return {"status": "error", "message": "At least one 'to' email is required"}
            
            if not subject:
                return {"status": "error", "message": "Email subject is required"}
            
            # Get PDF file path
            invoice_path = self._get_storage_path("invoice", storage_key)
            if not invoice_path.exists():
                # Fallback to assets directory
                assets_dir = Path(__file__).parent.parent.parent / "var" / "assets"
                invoice_path = assets_dir / storage_key
                if not invoice_path.exists():
                    return {"status": "error", "message": f"Invoice PDF file not found: {storage_key}"}
            
            # Send email using EmailHandlers
            result = self.email_handlers.handle_send_email_with_attachments(
                to=to_emails,
                cc=cc_emails,
                subject=subject,
                body=body,
                attachment_paths=[str(invoice_path)],
                user_id=user_id,
            )
            
            if result.get('status') == 'ok':
                # Update invoice status to SENT
                supabase.table("document").update({"status": "SENT"}).eq("id", invoice_id).execute()
                
                # Store sent email data in sent_email table
                opportunity_id = invoice.get('opportunity_id')
                sent_email_data = {
                    "document_id": invoice_id,
                    "opportunity_id": opportunity_id,
                    "from_email": "maalls@gmail.com",  # TODO: Get from authenticated user
                    "to_emails": to_emails,
                    "cc_emails": cc_emails if cc_emails else [],
                    "subject": subject,
                    "body": body,
                    "provider": "gmail",
                    "provider_message_id": result.get('message_id'),
                    "status": "sent",
                    "sent_at": datetime.now().isoformat(),
                    "attachment_names": [storage_key] if storage_key else [],
                    # "sent_by_user_id": user_id,  # TODO: Add when user auth is implemented
                }
                
                print(f"[BusinessHandlers] Preparing to insert sent_email data: {sent_email_data}")
                
                try:
                    insert_result = supabase.table("sent_email").insert(sent_email_data).execute()
                    print(f"[BusinessHandlers] Sent email record created for invoice {invoice_id}: {insert_result.data}")
                except Exception as e:
                    # Log error but don't fail the request - email was already sent
                    print(f"[BusinessHandlers] Warning: Failed to save sent_email record: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[BusinessHandlers] Invoice {invoice_id} sent successfully to {to_emails}")
                return {
                    "status": "ok",
                    "message": "Invoice sent successfully",
                    "recipients": to_emails,
                    "message_id": result.get('message_id')
                }
            else:
                return result
            
        except Exception as e:
            print(f"[BusinessHandlers] Error sending invoice {invoice_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error sending invoice: {str(e)}",
            }

    def handle_generate_invoice_pdf(self, document_id: str, user_id: str = None) -> Dict:
        """Generate a PDF for an existing invoice document and update storage_key."""
        supabase = get_supabase_service()

        try:
            # Load document with opportunity
            doc_resp = supabase.table("document").select("*").eq("id", document_id).single().execute()
            if getattr(doc_resp, "error", None):
                return {"status": "error", "message": f"Document lookup failed: {doc_resp.error}"}
            document = doc_resp.data
            if not document:
                return {"status": "error", "message": f"Document not found: {document_id}"}

            if document.get("type") != "INVOICE":
                return {"status": "error", "message": "PDF generation is only supported for invoices"}

            # Load opportunity and account
            opportunity_id = document.get("opportunity_id")
            account_id = None
            opportunity = {}
            account = {}
            
            if opportunity_id:
                opp_resp = supabase.table("opportunity").select("*").eq("id", opportunity_id).single().execute()
                if not getattr(opp_resp, "error", None) and opp_resp.data:
                    opportunity = opp_resp.data
                    account_id = opportunity.get("account_id")
                    
                    if account_id:
                        acc_resp = supabase.table("account").select("*").eq("id", account_id).single().execute()
                        if not getattr(acc_resp, "error", None) and acc_resp.data:
                            account = acc_resp.data
                            print(f"[BusinessHandlers] Loaded account: {account}")
                    else:
                        print(f"[BusinessHandlers] No account_id in opportunity {opportunity_id}")
                else:
                    print(f"[BusinessHandlers] Could not load opportunity {opportunity_id}")

            # Load lines
            line_resp = supabase.table("document_line").select("*").eq("document_id", document_id).order("position").execute()
            if getattr(line_resp, "error", None):
                return {"status": "error", "message": f"Document lines lookup failed: {line_resp.error}"}
            lines = line_resp.data or []

            # Build invoice-like structure for PDF generator
            invoice_data = {
                "invoice_id": document.get("id"),
                "external_ref": document.get("external_ref") or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "title": document.get("title") or "Invoice",
                "products": [],
                "contact": {
                    "company_name": account.get("name", ""),
                    "address": self._normalize_account_address(account),
                },
                "account": account,
                "issued_date": document.get("issued_at") or datetime.now().isoformat(),
                "currency": document.get("currency", "EUR"),
                "totals": {
                    "subtotal": float(document.get("total_excl_tax", 0)),
                    "tax": float(document.get("total_tax", 0)),
                    "total": float(document.get("total_incl_tax", 0)),
                }
            }

            for line in lines:
                invoice_data["products"].append({
                    "quantity": float(line.get("quantity", 1)),
                    "manufacturer": line.get("brand", ""),
                    "sku": line.get("sku"),
                    "description": line.get("description"),
                    "price": float(line.get("unit_price_excl_tax", 0)),
                    "tax_rate": float(line.get("tax_rate", 20)),
                    "unit": line.get("unit", "U"),
                })

            pdf_filename = self._generate_invoice_pdf(invoice_data)

            upd_resp = supabase.table("document").update({"storage_key": pdf_filename}).eq("id", document_id).execute()
            if getattr(upd_resp, "error", None):
                return {"status": "error", "message": f"Failed to update document with PDF: {upd_resp.error}"}

            return {
                "status": "ok",
                "storage_key": pdf_filename,
            }

        except Exception as e:  # noqa: BLE001
            print(f"[BusinessHandlers] Error generating PDF for invoice {document_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error generating PDF: {str(e)}",
            }

    def _generate_invoice_pdf(self, invoice_data: Dict) -> str:
        """Generate PDF from invoice data using HTML template.
        
        Parameters
        ----------
        invoice_data : Dict
            Invoice data with products, contact, invoice_id, etc.
        
        Returns
        -------
        str
            Filename of generated PDF
        """
        try:
            # Create invoices storage directory if it doesn't exist
            storage_dir = self._get_storage_dir("invoice")
            storage_dir.mkdir(parents=True, exist_ok=True)
            templates_dir = Path(__file__).parent.parent.parent / "templates"
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            invoice_id_num = str(uuid.uuid4())[:8]
            pdf_filename = f"invoice_{timestamp}_{invoice_id_num}.pdf"
            pdf_path = storage_dir / pdf_filename
            
            # Setup Jinja2 environment
            env = Environment(loader=FileSystemLoader(str(templates_dir)))
            
            # Add custom currency format filter
            def format_currency(value, currency):
                """Format number based on currency decimal places."""
                # Currencies with 0 decimal places
                if currency.upper() in ['JPY', 'YEN', 'KRW', 'CNY', 'RUB']:
                    decimals = 0
                # Currencies with 3 decimal places
                elif currency.upper() in ['BHD', 'JOD', 'KWD', 'OMR', 'TND']:
                    decimals = 3
                # Default to 2 decimal places
                else:
                    decimals = 2
                
                return f"{float(value):.{decimals}f}"
            
            env.filters['format_currency'] = format_currency
            template = env.get_template('invoice.html')
            
            # Prepare template data
            template_data = {
                'quote_id': invoice_data.get('external_ref', f"INV-{invoice_id_num}"),
                'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'issued_date': invoice_data.get('issued_date', ''),
                'title': invoice_data.get('title', ''),
                'contact': invoice_data.get('contact', {}),
                'account': invoice_data.get('account', {}),
                'products': [],
                'currency': invoice_data.get('currency', 'EUR'),
                'totals': invoice_data.get('totals', {}),
            }
            
            # Format products for template
            for product in invoice_data.get('products', []):
                template_data['products'].append({
                    'quantity': product.get('quantity', 1),
                    'manufacturer': product.get('manufacturer', ''),
                    'part_number': product.get('sku', ''),
                    'description': product.get('description', ''),
                    'price': product.get('price', 0),
                    'price_found': product.get('price', 0) > 0,
                })
            
            # Render HTML
            html_content = template.render(**template_data)
            
            # Generate PDF from HTML using WeasyPrint
            HTML(string=html_content).write_pdf(str(pdf_path))
            
            print(f"[BusinessHandlers] Invoice PDF saved to {pdf_path}")
            return pdf_filename
            
        except Exception as e:
            print(f"[BusinessHandlers] Error generating invoice PDF: {e}")
            import traceback
            traceback.print_exc()
            raise