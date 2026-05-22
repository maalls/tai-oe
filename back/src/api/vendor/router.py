from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_database_repository
from .schemas import VendorBrandResponse, VendorCreate, VendorResponse, VendorUpdate
from src.repository.database.repository import DatabaseRepository

router = APIRouter()


@router.get("/api/vendor", response_model=List[VendorResponse])
def list_vendors(db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT v.id, v.name, v.email, v.phone, v.website, v.created_at, v.updated_at,
               COALESCE(COUNT(DISTINCT b.id), 0)::int AS brand_count,
               COALESCE(COUNT(DISTINCT f.id), 0)::int AS family_count,
             COALESCE(COUNT(DISTINCT pf.product_id), 0)::int AS product_count
        FROM vendor v
        LEFT JOIN brand b ON b.vendor_id = v.id
        LEFT JOIN family f ON f.brand_id = b.id
        LEFT JOIN product_family pf ON pf.family_id = f.id
        GROUP BY v.id
        ORDER BY v.created_at DESC
        """
    )
    return rows


@router.get("/api/vendor/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT v.id, v.name, v.email, v.phone, v.website, v.created_at, v.updated_at,
               COALESCE(COUNT(DISTINCT b.id), 0)::int AS brand_count,
               COALESCE(COUNT(DISTINCT f.id), 0)::int AS family_count,
             COALESCE(COUNT(DISTINCT pf.product_id), 0)::int AS product_count
        FROM vendor v
        LEFT JOIN brand b ON b.vendor_id = v.id
        LEFT JOIN family f ON f.brand_id = b.id
        LEFT JOIN product_family pf ON pf.family_id = f.id
        WHERE v.id = %s
        GROUP BY v.id
        """,
        (vendor_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return rows[0]


@router.post("/api/vendor", response_model=VendorResponse)
def create_vendor(payload: VendorCreate, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        INSERT INTO vendor (name, email, phone, website)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, email, phone, website, created_at, updated_at,
                  0::int AS brand_count, 0::int AS family_count, 0::int AS product_count
        """,
        (payload.name, payload.email, payload.phone, payload.website),
    )
    return rows[0]


@router.put("/api/vendor/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: str,
    payload: VendorUpdate,
    db: DatabaseRepository = Depends(get_database_repository),
):
    fields = []
    values = []
    for field in ["name", "email", "phone", "website"]:
        value = getattr(payload, field)
        if value is not None:
            fields.append(f"{field} = %s")
            values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(vendor_id)
    rows = db.execute_dict_query(
        f"""
        UPDATE vendor
        SET {', '.join(fields)}, updated_at = now()
        WHERE id = %s
        RETURNING id, name, email, phone, website, created_at, updated_at
        """,
        tuple(values),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor = rows[0]
    count_rows = db.execute_dict_query(
        """
        SELECT COALESCE(COUNT(DISTINCT b.id), 0)::int AS brand_count,
               COALESCE(COUNT(DISTINCT f.id), 0)::int AS family_count,
             COALESCE(COUNT(DISTINCT pf.product_id), 0)::int AS product_count
        FROM vendor v
        LEFT JOIN brand b ON b.vendor_id = v.id
        LEFT JOIN family f ON f.brand_id = b.id
        LEFT JOIN product_family pf ON pf.family_id = f.id
        WHERE v.id = %s
        """,
        (vendor_id,),
    )
    counts = count_rows[0] if count_rows else {"brand_count": 0, "family_count": 0, "product_count": 0}
    vendor["brand_count"] = counts["brand_count"]
    vendor["family_count"] = counts["family_count"]
    vendor["product_count"] = counts["product_count"]
    return vendor


@router.delete("/api/vendor/{vendor_id}")
def delete_vendor(vendor_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query("DELETE FROM vendor WHERE id = %s RETURNING id", (vendor_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"id": rows[0]["id"]}


@router.get("/api/vendor/{vendor_id}/brands", response_model=List[VendorBrandResponse])
def list_vendor_brands(vendor_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT b.id, b.name, b.marque, b.website, b.target_margin, b.minimum_margin,
             COALESCE(COUNT(pf.product_id), 0)::int AS product_count
        FROM brand b
        LEFT JOIN family f ON f.brand_id = b.id
        LEFT JOIN product_family pf ON pf.family_id = f.id
        WHERE b.vendor_id = %s
        GROUP BY b.id
        ORDER BY b.name ASC
        """,
        (vendor_id,),
    )
    return rows
