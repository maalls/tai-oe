"""Application service for product operations."""

from typing import Any, Dict, List, Optional

from src.infrastructure.clients.database import DatabaseHandler
from src.infrastructure.config import create_database_handler


class ProductService:
    """Service orchestrating product list/create workflows."""

    def __init__(self, db_handler: Optional[DatabaseHandler] = None):
        self.db_handler = db_handler

    def _get_db_handler(self) -> DatabaseHandler:
        if self.db_handler is None:
            self.db_handler = create_database_handler(
                current_file=__file__,
                require_postgres_password=True,
            )
        return self.db_handler

    def list_products(self, qs: dict) -> List[Dict[str, Any]]:
        sku = qs.get("sku", [None])[0]
        limit = int(qs.get("limit", [10])[0])
        where_clause = ""
        params: List[Any] = []
        if sku:
            where_clause = "WHERE p.sku ILIKE %s"
            params.append(f"{str(sku).strip()}%")

        params.append(limit)
        rows = self._get_db_handler().execute_dict_query(
            f"""
            SELECT p.*,
                   to_jsonb(b) AS brand,
                   COALESCE(pf.family_links, '[]'::json) AS product_family
            FROM product p
            LEFT JOIN brand b ON b.id = p.brand_id
            LEFT JOIN LATERAL (
                SELECT json_agg(json_build_object('family', to_jsonb(f)) ORDER BY f.code) AS family_links
                FROM product_family pf
                JOIN family f ON f.id = pf.family_id
                WHERE pf.product_id = p.id
            ) pf ON true
            {where_clause}
            ORDER BY p.sku ASC
            LIMIT %s
            """,
            tuple(params),
        )
        return rows or []

    def create_family(self, family_code: str, brand_id: str) -> Dict[str, Any]:
        payload = {
            "brand_id": brand_id,
            "code": family_code,
            "type": family_code,
        }
        rows = self._get_db_handler().execute_dict_query(
            """
            INSERT INTO family (brand_id, code, type)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (payload["brand_id"], payload["code"], payload["type"]),
        )
        if not rows:
            raise RuntimeError("Failed to insert family")
        return rows[0]

    def post_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        product = self.upsert_product(payload)
        self.upsert_family(product, payload)
        return product

    def _resolve_brand(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        db_handler = self._get_db_handler()
        brand_id = payload.get("brand_id")
        if brand_id:
            brands = db_handler.execute_dict_query(
                "SELECT * FROM brand WHERE id = %s LIMIT 1",
                (brand_id,),
            )
            if brands:
                return brands[0]

        brands = db_handler.execute_dict_query(
            "SELECT * FROM brand WHERE marque = %s LIMIT 1",
            (payload["marque"],),
        )
        if not brands:
            brands = db_handler.execute_dict_query(
                "SELECT * FROM brand WHERE name = %s LIMIT 1",
                (payload["marque"],),
            )
        if not brands:
            raise ValueError(f"Brand '{payload['marque']}' not found in database")
        return brands[0]

    def _resolve_batch(self, payload: Dict[str, Any]) -> int:
        batch = int(payload.get("batch") or 1)
        if batch < 1:
            raise ValueError("Batch must be greater than or equal to 1")
        return batch

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        rows = self._get_db_handler().execute_dict_query(
            """
            SELECT p.*,
                   to_jsonb(b) AS brand,
                   COALESCE(pf.family_links, '[]'::json) AS product_family,
                   COALESCE(pm.media_rows, '[]'::json) AS product_media
            FROM product p
            LEFT JOIN brand b ON b.id = p.brand_id
            LEFT JOIN LATERAL (
                SELECT json_agg(json_build_object('family', to_jsonb(f)) ORDER BY f.code) AS family_links
                FROM product_family pf
                JOIN family f ON f.id = pf.family_id
                WHERE pf.product_id = p.id
            ) pf ON true
            LEFT JOIN LATERAL (
                SELECT json_agg(to_jsonb(pm) ORDER BY pm.position NULLS LAST, pm.created_at) AS media_rows
                FROM product_media pm
                WHERE pm.product_id = p.id
            ) pm ON true
            WHERE p.id = %s
            LIMIT 1
            """,
            (product_id,),
        )
        return rows[0] if rows else None

    def update_product(self, product_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = ["family_codes", "libelle240", "marque", "refciale", "tarif", "vector_text"]
        for field in fields:
            if field not in payload:
                raise ValueError(f"Missing product field: {field}")

        brand = self._resolve_brand(payload)

        update_data = {
            "sku": payload["refciale"],
            "name": payload["libelle240"],
            "brand_id": brand["id"],
            "price": payload["tarif"],
            "batch": self._resolve_batch(payload),
        }

        update_result = self._get_db_handler().execute_dict_query(
            """
            UPDATE product
            SET sku = %s,
                name = %s,
                brand_id = %s,
                price = %s,
                batch = %s
            WHERE id = %s
            RETURNING *
            """,
            (
                update_data["sku"],
                update_data["name"],
                update_data["brand_id"],
                update_data["price"],
                update_data["batch"],
                product_id,
            ),
        )
        if not update_result:
            raise RuntimeError("Failed to update product in database")

        product = update_result[0]
        product["brand"] = brand

        self._get_db_handler().execute_update(
            "DELETE FROM product_family WHERE product_id = %s",
            (product_id,),
        )
        self.upsert_family(product, payload)

        return product

    def upsert_family(self, product: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        brand_id = (product.get("brand") or {}).get("id") or product.get("brand_id")
        if not brand_id:
            raise ValueError("Missing product brand_id for family upsert")

        family_codes = payload.get("family_codes") or []
        if not family_codes:
            product["families"] = []
            return product

        placeholders = ", ".join(["%s"] * len(family_codes))
        params: List[Any] = [brand_id, *family_codes]
        families = self._get_db_handler().execute_dict_query(
            f"""
            SELECT *
            FROM family
            WHERE brand_id = %s
              AND code IN ({placeholders})
            """,
            tuple(params),
        )
        existing_codes = {family["code"] for family in families}
        missing_codes = [code for code in family_codes if code not in existing_codes]

        if missing_codes:
            missing_codes_text = ", ".join(sorted(missing_codes))
            raise ValueError(
                f"Unknown family code(s) for brand '{brand_id}': {missing_codes_text}"
            )

        for code in family_codes:
            family = next(f for f in families if f["code"] == code)

            self._get_db_handler().execute_update(
                """
                INSERT INTO product_family (product_id, family_id)
                SELECT %s, %s
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM product_family
                    WHERE product_id = %s AND family_id = %s
                )
                """,
                (product["id"], family["id"], product["id"], family["id"]),
            )

        product["families"] = families
        return product

    def upsert_product(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fields = ["family_codes", "libelle240", "marque", "refciale", "tarif", "vector_text"]
        for field in fields:
            if field not in payload:
                raise ValueError(f"Missing product field: {field}")

        brand = self._resolve_brand(payload)

        products = self._get_db_handler().execute_dict_query(
            "SELECT * FROM product WHERE sku = %s LIMIT 1",
            (payload["refciale"],),
        )
        if products:
            product = products[0]
        else:
            data = {
                "sku": payload["refciale"],
                "name": payload["libelle240"],
                "brand_id": brand["id"],
                "price": payload["tarif"],
                "batch": self._resolve_batch(payload),
            }
            insert_result = self._get_db_handler().execute_dict_query(
                """
                INSERT INTO product (sku, name, brand_id, price, batch)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (data["sku"], data["name"], data["brand_id"], data["price"], data["batch"]),
            )
            if not insert_result:
                raise RuntimeError("Failed to insert product into database")
            product = insert_result[0]

        product["brand"] = brand
        return product
