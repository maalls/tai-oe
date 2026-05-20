"""Application service for product operations."""

from typing import Any, Dict, List, Optional

from src.infrastructure.clients.supabase import get_supabase_service


class ProductService:
    """Service orchestrating product list/create workflows."""

    def __init__(self, supabase=None):
        self.supabase = supabase or get_supabase_service()

    def list_products(self, qs: dict) -> List[Dict[str, Any]]:
        sku = qs.get("sku", [None])[0]
        limit = int(qs.get("limit", [10])[0])
        query = self.supabase.from_("product").select("*,brand(*),product_family(*,family(*))")
        if sku:
            query = query.ilike("sku", f"{sku}")
        query = query.limit(limit)
        result = query.execute()
        return result.data if result and result.data else []

    def post_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        product = self.upsert_product(payload)
        self.upsert_family(product, payload)
        return product

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        result = (
            self.supabase
            .from_("product")
            .select("*,brand(*),product_family(*,family(*))")
            .eq("id", product_id)
            .maybe_single()
            .execute()
        )
        return result.data if result and result.data else None

    def update_product(self, product_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = ["family_codes", "libelle240", "marque", "refciale", "tarif", "vector_text"]
        for field in fields:
            if field not in payload:
                raise ValueError(f"Missing product field: {field}")

        brands = self.supabase.from_("brand").select("*").eq("marque", payload["marque"]).execute()
        if not brands.data:
            brands = self.supabase.from_("brand").select("*").eq("name", payload["marque"]).execute()
        if not brands.data:
            raise ValueError(f"Brand '{payload['marque']}' not found in database")
        brand = brands.data[0]

        update_data = {
            "sku": payload["refciale"],
            "name": payload["libelle240"],
            "brand_id": brand["id"],
            "price": payload["tarif"],
        }

        update_result = self.supabase.from_("product").update(update_data).eq("id", product_id).execute()
        if not update_result.data:
            raise RuntimeError("Failed to update product in database")

        product = update_result.data[0]
        product["brand"] = brand

        self.supabase.from_("product_family").delete().eq("product_id", product_id).execute()
        self.upsert_family(product, payload)

        return product

    def upsert_family(self, product: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = (product.get("brand") or {}).get("id") or product.get("brand_id")
        if not brand_id:
            raise ValueError("Missing product brand_id for family upsert")

        family_codes = payload.get("family_codes") or []
        db_families = (
            self.supabase
            .from_("family")
            .select("*")
            .eq("brand_id", brand_id)
            .in_("code", family_codes)
            .execute()
        )
        families = db_families.data or []
        existing_codes = {family["code"] for family in families}

        for code in family_codes:
            if code not in existing_codes:
                family = self.create_family(code, brand_id)
                families.append(family)
            else:
                family = next(f for f in families if f["code"] == code)

            result = self.supabase.from_("product_family").upsert(
                {"product_id": product["id"], "family_id": family["id"]}
            ).execute()
            if result.data is None:
                raise RuntimeError("Failed to link product to family code in database")

        product["families"] = families
        return product

    def create_family(self, code: str, brand_id: str) -> Dict[str, Any]:
        data = {"brand_id": brand_id, "code": code, "type": "NET_PRICE", "name": code}
        result = self.supabase.from_("family").insert(data).execute()
        if result.data is None:
            raise RuntimeError("Failed to create family code in database")
        return result.data[0]

    def upsert_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = ["family_codes", "libelle240", "marque", "refciale", "tarif", "vector_text"]
        for field in fields:
            if field not in payload:
                raise ValueError(f"Missing product field: {field}")

        brands = self.supabase.from_("brand").select("*").eq("marque", payload["marque"]).execute()
        if not brands.data:
            raise ValueError(f"Brand '{payload['marque']}' not found in database")
        brand = brands.data[0]

        products = self.supabase.from_("product").select("*").eq("sku", payload["refciale"]).execute()
        if products.data:
            product = products.data[0]
        else:
            data = {
                "sku": payload["refciale"],
                "name": payload["libelle240"],
                "brand_id": brand["id"],
                "price": payload["tarif"],
            }
            insert_result = self.supabase.from_("product").insert(data).execute()
            if insert_result.data:
                product = insert_result.data[0]
            else:
                raise RuntimeError("Failed to insert product into database")

        product["brand"] = brand
        return product
