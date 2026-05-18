from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.repository.database.repository import DatabaseRepository
from .schemas import BrandCreate, BrandFamilyResponse, BrandResponse, BrandUpdate

router = APIRouter()


def get_db():
    return DatabaseRepository()


@router.get('/api/brand/{brand_id}', response_model=BrandResponse)
def get_brand(brand_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vendor_id, website, email, phone, minimum_margin, target_margin, created_at, updated_at
        FROM brand
        WHERE id = %s
        """,
        (brand_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail='Brand not found')
    return rows[0]


@router.post('/api/brand', response_model=BrandResponse)
def create_brand(payload: BrandCreate, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        INSERT INTO brand (name, website, email, phone, minimum_margin, target_margin, marque, vendor_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, vendor_id, website, email, phone, minimum_margin, target_margin, created_at, updated_at
        """,
        (
            payload.name,
            payload.website,
            payload.email,
            payload.phone,
            payload.minimum_margin,
            payload.target_margin,
            payload.name,
            payload.vendor_id,
        ),
    )
    return rows[0]


@router.put('/api/brand/{brand_id}', response_model=BrandResponse)
def update_brand(brand_id: str, payload: BrandUpdate, db=Depends(get_db)):
    fields = []
    values = []
    for field in ['name', 'vendor_id', 'website', 'email', 'phone', 'minimum_margin', 'target_margin']:
        value = getattr(payload, field)
        if value is not None:
            fields.append(f'{field} = %s')
            values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail='No fields to update')

    values.append(brand_id)
    rows = db.execute_dict_query(
        f"""
        UPDATE brand
        SET {', '.join(fields)}, updated_at = now()
        WHERE id = %s
        RETURNING id, name, vendor_id, website, email, phone, minimum_margin, target_margin, created_at, updated_at
        """,
        tuple(values),
    )
    if not rows:
        raise HTTPException(status_code=404, detail='Brand not found')
    return rows[0]


@router.get('/api/brand/{brand_id}/families', response_model=List[BrandFamilyResponse])
def list_brand_families(brand_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT f.id,
               f.name,
               f.code,
               f.type,
               f.brand_id,
               f.product_code,
               f.quantity,
               f.discount,
               f.minimum_margin,
               f.target_margin,
               f.unit,
               f.packing,
               f.lead_time_week,
               f.net_price,
               COALESCE(COUNT(pf.product_id), 0)::int AS product_family_count,
               p.id AS product_id,
               p.sku AS product_sku,
               p.name AS product_name,
               p.price AS product_price,
               p.brand_id AS product_brand_id
        FROM family f
        LEFT JOIN product_family pf ON pf.family_id = f.id
        LEFT JOIN product p ON p.sku = f.product_code
        WHERE f.brand_id = %s
        GROUP BY f.id, p.id, p.sku, p.name, p.price, p.brand_id
        ORDER BY f.name ASC
        """,
        (brand_id,),
    )
    return [
        {
            'id': row.get('id'),
            'name': row.get('name'),
            'code': row.get('code'),
            'type': row.get('type'),
            'brand_id': row.get('brand_id'),
            'product_code': row.get('product_code'),
            'quantity': row.get('quantity'),
            'discount': row.get('discount'),
            'minimum_margin': row.get('minimum_margin'),
            'target_margin': row.get('target_margin'),
            'unit': row.get('unit'),
            'packing': row.get('packing'),
            'lead_time_week': row.get('lead_time_week'),
            'net_price': row.get('net_price'),
            'product_family_count': row.get('product_family_count', 0),
            'product': {
                'id': row.get('product_id'),
                'sku': row.get('product_sku'),
                'name': row.get('product_name'),
                'price': row.get('product_price'),
                'brand_id': row.get('product_brand_id'),
            }
            if row.get('product_id') and row.get('product_sku')
            else None,
        }
        for row in rows
    ]
