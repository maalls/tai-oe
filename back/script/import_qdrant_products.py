"""Import Qdrant product entries into the product table."""

import argparse
import os
from datetime import date
from typing import Dict, List, Optional, Tuple

from src.controller.db_client import DatabaseHandler
from src.controller.qdrant_handler import QdrantHandler
from src.supabase.supabase_client import get_supabase_service


def _fetch_marques_by_fabricant(db: DatabaseHandler, fabricant: str) -> List[str]:
    """Get all marques associated with a fabricant from cartouches."""
    rows = db.execute_dict_query(
        "SELECT DISTINCT carmarque FROM fabdis_cartouches WHERE LOWER(TRIM(fabricant)) = LOWER(TRIM(%s))",
        (fabricant,)
    )
    return [row['carmarque'] for row in rows if row.get('carmarque')]


def _normalize(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return value.strip().lower()


def _serialize_date(value: Optional[object]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def _fetch_mkt_codes(
    db: DatabaseHandler,
    marque: str,
    refciale: str,
    cache: Dict[Tuple[str, str], List[str]],
) -> List[str]:
    cache_key = (marque, refciale)
    if cache_key in cache:
        return cache[cache_key]

    rows = db.execute_dict_query(
        """
        SELECT mkt1, mkt2, mkt3, mkt4, mkt5
        FROM fabdis_commerce
        WHERE LOWER(TRIM(marque)) = LOWER(TRIM(%s))
          AND refciale = %s
        LIMIT 1
        """,
        (marque, refciale),
    )
    codes: List[str] = []
    if rows:
        row = rows[0]
        for key in ("mkt1", "mkt2", "mkt3", "mkt4", "mkt5"):
            value = row.get(key)
            if isinstance(value, str):
                code = value.strip()
                if code:
                    codes.append(code)
    cache[cache_key] = codes
    return codes


def _fetch_pyramide_names(
    db: DatabaseHandler,
    marque: str,
    codes: List[str],
) -> Dict[str, str]:
    if not codes:
        return {}

    placeholders = ",".join(["%s"] * len(codes))
    params: List[object] = [marque, *codes, *codes]
    rows = db.execute_dict_query(
        f"""
        SELECT mktc, mkt, mktl
        FROM fabdis_pyramide
        WHERE LOWER(TRIM(marquep)) = LOWER(TRIM(%s))
          AND (mktc IN ({placeholders}) OR mkt IN ({placeholders}))
        """,
        tuple(params),
    )
    names: Dict[str, str] = {}
    for row in rows:
        code = row.get("mktc") or row.get("mkt")
        if not code:
            continue
        name = row.get("mktl") or row.get("mkt") or code
        names[str(code).strip()] = str(name).strip()
    return names


def _get_or_create_family(
    supabase,
    cache: Dict[Tuple[str, str], str],
    brand_id: str,
    code: str,
    name: str,
) -> Optional[str]:
    cache_key = (brand_id, code)
    if cache_key in cache:
        return cache[cache_key]

    result = (
        supabase.table("family")
        .select("id")
        .eq("brand_id", brand_id)
        .eq("code", code)
        .eq("type", "discount")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if rows:
        family_id = rows[0].get("id")
        if family_id:
            cache[cache_key] = family_id
            return family_id

    payload = {
        "brand_id": brand_id,
        "name": name,
        "code": code,
        "type": "discount",
    }
    supabase.table("family").insert(payload).execute()
    result = (
        supabase.table("family")
        .select("id")
        .eq("brand_id", brand_id)
        .eq("code", code)
        .eq("type", "discount")
        .limit(1)
        .execute()
    )
    rows = result.data or []
    if rows:
        family_id = rows[0].get("id")
        if family_id:
            cache[cache_key] = family_id
            return family_id
    return None


def _insert_product_family_links(
    supabase,
    links: List[Tuple[str, str]],
) -> None:
    if not links:
        return

    rows = [
        {
            "product_id": product_id,
            "family_id": family_id,
        }
        for product_id, family_id in links
    ]
    supabase.table("product_family").upsert(
        rows,
        on_conflict="product_id,family_id",
    ).execute()


def _fetch_product_ids(supabase, skus: List[str]) -> Dict[str, str]:
    if not skus:
        return {}

    product_ids: Dict[str, str] = {}
    chunk_size = 500
    for start in range(0, len(skus), chunk_size):
        chunk = skus[start:start + chunk_size]
        result = (
            supabase.table("product")
            .select("id,sku")
            .in_("sku", chunk)
            .execute()
        )
        rows = result.data or []
        for row in rows:
            sku = row.get("sku")
            product_id = row.get("id")
            if sku and product_id:
                product_ids[sku] = product_id
    return product_ids


def _load_product_columns(supabase) -> List[str]:
    # Fallback to common columns when information_schema is not accessible
    return [
        "sku",
        "name",
        "brand_id",
        "price",
        "fabdis_appli_date",
        "fabdis_edited_date",
        "default_unit",
        "default_tax_rate",
    ]


def _extract_missing_column(error: Exception) -> Optional[str]:
    message = str(error)
    marker = "Could not find the '"
    if marker not in message or " column of 'product'" not in message:
        return None
    start = message.find(marker) + len(marker)
    end = message.find("' column of 'product'", start)
    if end == -1:
        return None
    return message[start:end]


def _safe_upsert(supabase, records: List[Dict], columns: List[str], mode: str) -> None:
    if not records:
        return

    try:
        if mode == "update":
            _safe_update(supabase, records, columns)
            return

        if "sku" in columns:
            supabase.table("product").upsert(records, on_conflict="sku").execute()
        else:
            supabase.table("product").insert(records).execute()
        return
    except Exception as exc:
        missing = _extract_missing_column(exc)
        if not missing or missing not in columns:
            raise

        filtered = [{k: v for k, v in record.items() if k != missing} for record in records]
        columns.remove(missing)
        if mode == "update":
            _safe_update(supabase, filtered, columns)
            return

        if "sku" in columns:
            supabase.table("product").upsert(filtered, on_conflict="sku").execute()
        else:
            supabase.table("product").insert(filtered).execute()


def _safe_update(supabase, records: List[Dict], columns: List[str]) -> None:
    if not records:
        return

    if "sku" not in columns:
        raise ValueError("Update mode requires sku column in product table")

    for record in records:
        sku = record.get("sku")
        if not sku:
            continue
        update_payload = {k: v for k, v in record.items() if k != "sku"}
        if not update_payload:
            continue
        supabase.table("product").update(update_payload).eq("sku", sku).execute()


def _load_brand_lookup(supabase) -> Dict[str, str]:
    try:
        result = supabase.table("brand").select("id,name").execute()
        return {
            row["name"].strip().lower(): row["id"]
            for row in (result.data or [])
            if row.get("name")
        }
    except Exception:
        return {}


def _load_vendor_lookup(supabase) -> Dict[str, str]:
    try:
        result = supabase.table("vendor").select("id,name").execute()
        return {
            row["name"].strip().lower(): row["id"]
            for row in (result.data or [])
            if row.get("name")
        }
    except Exception:
        return {}


def _fetch_fabricant(db: DatabaseHandler, supabase, marque: str) -> Optional[str]:
    try:
        rows = db.execute_dict_query(
            """
            SELECT fabricant
            FROM fabdis_cartouches
            WHERE LOWER(TRIM(carmarque)) = LOWER(TRIM(%s))
            LIMIT 1
            """,
            (marque,),
        )
        if rows:
            return rows[0].get("fabricant")
    except Exception:
        pass
    return None


def _fetch_cartouche_dates(db: DatabaseHandler, marque: str) -> Dict[str, Optional[str]]:
    try:
        rows = db.execute_dict_query(
            """
            SELECT dateappli, datedit
            FROM fabdis_cartouches
            WHERE LOWER(TRIM(carmarque)) = LOWER(TRIM(%s))
            LIMIT 1
            """,
            (marque,),
        )
        if rows:
            return {
                "fabdis_appli_date": rows[0].get("dateappli"),
                "fabdis_edited_date": rows[0].get("datedit"),
            }
    except Exception:
        pass
    return {
        "fabdis_appli_date": None,
        "fabdis_edited_date": None,
    }


def _ensure_brand_vendor(
    supabase,
    brand_lookup: Dict[str, str],
    vendor_lookup: Dict[str, str],
    fabricant_cache: Dict[str, Optional[str]],
    db: DatabaseHandler,
    marque: str,
) -> tuple[Dict[str, str], Dict[str, str]]:
    marque_key = _normalize(marque)
    if not marque_key:
        return brand_lookup, vendor_lookup

    if marque_key not in fabricant_cache:
        fabricant_cache[marque_key] = _fetch_fabricant(db, supabase, marque)

    fabricant = fabricant_cache.get(marque_key)
    if not fabricant:
        if marque_key not in fabricant_cache:
            raise RuntimeError(
                f"Missing FABRICANT for marque '{marque}' in fabdis_cartouches"
            )
        fabricant = _fetch_fabricant(db, supabase, marque)
        fabricant_cache[marque_key] = fabricant
    if not fabricant:
        raise RuntimeError(f"Missing FABRICANT for marque '{marque}' in fabdis_cartouches")

    vendor_key = _normalize(fabricant)
    if not vendor_key:
        raise RuntimeError(f"Invalid FABRICANT value for marque '{marque}'")

    vendor_id = vendor_lookup.get(vendor_key)
    if not vendor_id:
        supabase.table("vendor").insert({"name": fabricant}).execute()
        vendor_lookup = _load_vendor_lookup(supabase)
        vendor_id = vendor_lookup.get(vendor_key)
    if not vendor_id:
        raise RuntimeError(f"Vendor not found after insert for '{fabricant}'")

    brand_id = brand_lookup.get(marque_key)
    if brand_id:
        supabase.table("brand").update({"vendor_id": vendor_id}).eq("id", brand_id).execute()
    else:
        brand_payload: Dict[str, object] = {
            "name": marque,
            "marque": marque,
            "vendor_id": vendor_id,
        }
        supabase.table("brand").insert(brand_payload).execute()
        brand_lookup = _load_brand_lookup(supabase)

    return brand_lookup, vendor_lookup


def _build_product_record(payload: Dict, columns: List[str], brand_lookup: Dict[str, str]) -> Optional[Dict]:
    sku = payload.get("sku") or payload.get("refciale")
    if not sku:
        return None

    name = payload.get("name") or payload.get("libelle240") or sku
    brand_name = payload.get("marque") or payload.get("brand")

    record: Dict[str, object] = {}

    if "sku" in columns:
        record["sku"] = sku
    if "name" in columns:
        record["name"] = name
    if "default_unit" in columns and "default_unit" not in record:
        record["default_unit"] = "U"
    if "default_tax_rate" in columns and "default_tax_rate" not in record:
        record["default_tax_rate"] = 20

    if "price" in columns:
        raw_price = payload.get("price")
        if raw_price is None:
            raw_price = payload.get("tarif")
        if raw_price is not None:
            try:
                record["price"] = float(raw_price)
            except (TypeError, ValueError):
                pass

    if "brand_id" in columns:
        brand_key = _normalize(brand_name)
        if brand_key and brand_key in brand_lookup:
            record["brand_id"] = brand_lookup[brand_key]

    return record


def import_qdrant_products(
    collection: str,
    url: Optional[str],
    batch_size: int,
    max_records: Optional[int],
    dry_run: bool,
    mode: str,
    marque: Optional[str],
) -> None:
    supabase = get_supabase_service()
    columns = _load_product_columns(supabase)
    brand_lookup = _load_brand_lookup(supabase) if "brand_id" in columns else {}
    vendor_lookup = _load_vendor_lookup(supabase) if "brand_id" in columns else {}
    db = DatabaseHandler() if "brand_id" in columns else None
    fabricant_cache: Dict[str, Optional[str]] = {}
    cartouche_cache: Dict[str, Dict[str, Optional[str]]] = {}
    mkt_cache: Dict[Tuple[str, str], List[str]] = {}
    pyramide_cache: Dict[str, Dict[str, str]] = {}
    family_cache: Dict[Tuple[str, str], str] = {}

    handler = QdrantHandler(url=url, collection_name=collection)
    if not handler.test_connection():
        raise RuntimeError("Qdrant connection failed")

    offset = None
    total_imported = 0
    total_seen = 0

    while True:
        scroll_kwargs = {
            "limit": batch_size,
            "offset": offset,
            "with_payload": True,
            "with_vectors": False,
        }
        if marque:
            scroll_kwargs["filters"] = {
                "marque": marque,
            }
        result = handler.scroll_points(**scroll_kwargs)
        points = result.get("points", [])
        offset = result.get("next_offset")

        if not points:
            break

        payloads = [point.get("payload") or {} for point in points]

        records: List[Dict] = []
        family_targets: List[Tuple[str, str, str]] = []
        for payload in payloads:
            marque = payload.get("marque") or payload.get("brand")
            if marque and "brand_id" in columns and db is not None:
                brand_lookup, vendor_lookup = _ensure_brand_vendor(
                    supabase,
                    brand_lookup,
                    vendor_lookup,
                    fabricant_cache,
                    db,
                    marque,
                )
            record = _build_product_record(payload, columns, brand_lookup)
            if record and marque and db is not None:
                marque_key = _normalize(marque)
                if marque_key and marque_key not in cartouche_cache:
                    cartouche_cache[marque_key] = _fetch_cartouche_dates(db, marque)
                dates = cartouche_cache.get(marque_key, {})
                if "fabdis_appli_date" in columns and dates.get("fabdis_appli_date"):
                    record["fabdis_appli_date"] = _serialize_date(dates["fabdis_appli_date"])
                if "fabdis_edited_date" in columns and dates.get("fabdis_edited_date"):
                    record["fabdis_edited_date"] = _serialize_date(dates["fabdis_edited_date"])
                brand_id = record.get("brand_id")
                sku = record.get("sku")
                if brand_id and sku and marque:
                    family_targets.append((str(brand_id), marque, str(sku)))
            if record:
                records.append(record)

        total_seen += len(points)

        if records:
            if dry_run:
                total_imported += len(records)
            else:
                _safe_upsert(supabase, records, columns, mode)
                total_imported += len(records)

        if records and not dry_run and db is not None and family_targets:
            skus = [record.get("sku") for record in records if record.get("sku")]
            product_ids = _fetch_product_ids(supabase, skus)

            links: List[Tuple[str, str]] = []
            for brand_id, marque, sku in family_targets:
                product_id = product_ids.get(sku)
                if not product_id:
                    continue
                codes = _fetch_mkt_codes(db, marque, sku, mkt_cache)
                if not codes:
                    continue
                marque_key = _normalize(marque) or marque
                names_by_code = pyramide_cache.get(marque_key, {})
                missing_codes = [code for code in codes if code not in names_by_code]
                if missing_codes:
                    fetched = _fetch_pyramide_names(db, marque, missing_codes)
                    names_by_code = {**names_by_code, **fetched}
                    pyramide_cache[marque_key] = names_by_code
                for code in codes:
                    family_name = names_by_code.get(code, code)
                    family_id = _get_or_create_family(
                        supabase,
                        family_cache,
                        brand_id,
                        code,
                        family_name,
                    )
                    if family_id:
                        links.append((product_id, family_id))

            _insert_product_family_links(supabase, links)

        if max_records and total_seen >= max_records:
            break

        if offset is None:
            break

    print(
        f"Imported {total_imported} product record(s) from {total_seen} Qdrant point(s)"
        + (" (dry-run)" if dry_run else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Qdrant product entries into product table")
    parser.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION", "test_commerce_vectors"))
    parser.add_argument("--url", default=os.getenv("QDRANT_URL"))
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fabricant", help="Import all marques for a fabricant (e.g., ABB)")
    parser.add_argument("--marque", help="Import only products matching this marque")
    parser.add_argument(
        "--mode",
        choices=["upsert", "update"],
        default="upsert",
        help="Choose whether to upsert records or update existing rows by sku",
    )

    args = parser.parse_args()

    # Resolve marques from fabricant if provided
    marques_to_import = None
    if args.fabricant:
        db = DatabaseHandler()
        marques_to_import = _fetch_marques_by_fabricant(db, args.fabricant)
        if not marques_to_import:
            print(f"❌ No marques found for fabricant '{args.fabricant}'")
            return
        print(f"✓ Found {len(marques_to_import)} marque(s) for '{args.fabricant}': {', '.join(marques_to_import)}")
        
        # Import each marque
        for marque in marques_to_import:
            print(f"\n📥 Importing {marque}...")
            import_qdrant_products(
                collection=args.collection,
                url=args.url,
                batch_size=args.batch_size,
                max_records=args.max_records,
                dry_run=args.dry_run,
                mode=args.mode,
                marque=marque,
            )
    else:
        # Use specific marque or import all if no marque specified
        import_qdrant_products(
            collection=args.collection,
            url=args.url,
            batch_size=args.batch_size,
            max_records=args.max_records,
            dry_run=args.dry_run,
            mode=args.mode,
            marque=args.marque,
        )


if __name__ == "__main__":
    main()
