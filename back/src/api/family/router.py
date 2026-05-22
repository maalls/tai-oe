from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_database_repository
from src.repository.repository import DatabaseRepository

router = APIRouter()


def _sync_net_price_family_link(db: DatabaseRepository, family_id: str, product_code: str | None) -> None:
    if not product_code:
        db.execute_dict_query(
            "DELETE FROM product_family WHERE family_id = %s",
            (family_id,),
        )
        return

    product_rows = db.execute_dict_query(
        """
        SELECT id, sku, name, price, brand_id
        FROM product
        WHERE sku = %s
        LIMIT 1
        """,
        (product_code,),
    )
    if not product_rows:
        db.execute_dict_query(
            "DELETE FROM product_family WHERE family_id = %s",
            (family_id,),
        )
        return

    product_id = product_rows[0]["id"]
    db.execute_dict_query(
        """
        INSERT INTO product_family (product_id, family_id)
        VALUES (%s, %s)
        ON CONFLICT (product_id, family_id) DO NOTHING
        """,
        (product_id, family_id),
    )
    db.execute_dict_query(
        """
        DELETE FROM product_family
        WHERE family_id = %s AND product_id <> %s
        """,
        (family_id, product_id),
    )


def _resolve_family_discount_document_id(db: DatabaseRepository, family_id: str) -> tuple[str, str | None]:
    rows = db.execute_dict_query(
        """
        SELECT f.id AS family_id,
               (
                   SELECT d.id
                   FROM document d
                   WHERE d.type = 'FAMILY_DISCOUNT' AND d.external_ref = f.brand_id
                   ORDER BY d.created_at ASC
                   LIMIT 1
               ) AS document_id
        FROM family f
        WHERE f.id = %s
        """,
        (family_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail='Family not found')

    row = rows[0]
    return row['family_id'], row.get('document_id')


@router.get('/api/family/{family_id}')
def get_family(family_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, code, type, brand_id, product_code, quantity, discount,
               minimum_margin, target_margin, unit, packing, lead_time_week, net_price,
               created_at, updated_at
        FROM family
        WHERE id = %s
        """,
        (family_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail='Family not found')
    return rows[0]


@router.post('/api/family')
def create_family(payload: dict, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        INSERT INTO family (
            name, code, type, brand_id, product_code, quantity, discount,
            minimum_margin, target_margin, unit, packing, lead_time_week, net_price
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, code, type, brand_id, product_code, quantity, discount,
                  minimum_margin, target_margin, unit, packing, lead_time_week, net_price,
                  created_at, updated_at
        """,
        (
            payload.get('name'),
            payload.get('code'),
            payload['type'],
            payload['brand_id'],
            payload.get('product_code'),
            payload.get('quantity'),
            payload.get('discount'),
            payload.get('minimum_margin'),
            payload.get('target_margin'),
            payload.get('unit'),
            payload.get('packing'),
            payload.get('lead_time_week'),
            payload.get('net_price'),
        ),
    )
    return rows[0]


@router.put('/api/family/{family_id}')
def update_family(
    family_id: str,
    payload: dict,
    db: DatabaseRepository = Depends(get_database_repository),
):
    fields = []
    values = []
    for field in [
        'name',
        'code',
        'type',
        'brand_id',
        'product_code',
        'quantity',
        'discount',
        'minimum_margin',
        'target_margin',
        'unit',
        'packing',
        'lead_time_week',
        'net_price',
    ]:
        if field in payload:
            fields.append(f'{field} = %s')
            values.append(payload[field])

    if not fields:
        raise HTTPException(status_code=400, detail='No fields to update')

    values.append(family_id)
    rows = db.execute_dict_query(
        f"""
        UPDATE family
        SET {', '.join(fields)}, updated_at = now()
        WHERE id = %s
        RETURNING id, name, code, type, brand_id, product_code, quantity, discount,
                  minimum_margin, target_margin, unit, packing, lead_time_week, net_price,
                  created_at, updated_at
        """,
        tuple(values),
    )
    if not rows:
        raise HTTPException(status_code=404, detail='Family not found')

    family = rows[0]
    if (family.get('type') or '').lower() == 'net_price':
        _sync_net_price_family_link(db, family_id, family.get('product_code'))
    return family


@router.delete('/api/family/{family_id}')
def delete_family(family_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    db.execute_dict_query(
        'DELETE FROM product_family WHERE family_id = %s',
        (family_id,),
    )
    rows = db.execute_dict_query('DELETE FROM family WHERE id = %s RETURNING id', (family_id,))
    if not rows:
        raise HTTPException(status_code=404, detail='Family not found')
    return {'id': rows[0]['id']}


@router.get('/api/family/{family_id}/discount-lines')
def list_family_discount_lines(
    family_id: str,
    db: DatabaseRepository = Depends(get_database_repository),
):
    _, document_id = _resolve_family_discount_document_id(db, family_id)
    if not document_id:
        return {'document_id': None, 'lines': []}

    rows = db.execute_dict_query(
        """
        SELECT id,
               position,
               quantity,
               unit,
               unit_price_excl_tax,
               discount_rate,
               sku,
               line_total_excl_tax
        FROM document_line
        WHERE document_id = %s
        ORDER BY position ASC
        """,
        (document_id,),
    )
    return {'document_id': document_id, 'lines': rows}


@router.put('/api/family/{family_id}/discount-lines')
def save_family_discount_lines(
    family_id: str,
    payload: dict,
    db: DatabaseRepository = Depends(get_database_repository),
):
    _, document_id = _resolve_family_discount_document_id(db, family_id)
    if not document_id:
        raise HTTPException(status_code=400, detail='No FAMILY_DISCOUNT document found for this family')

    lines = payload.get('lines') or []
    for line in lines:
        line_id = str(line.get('id') or '')
        params = (
            line.get('position'),
            line.get('sku') or None,
            line.get('quantity') or 1,
            line.get('unit') or 'U',
            line.get('unit_price_excl_tax') or 0,
            line.get('discount_rate') or 0,
            line.get('line_total_excl_tax') or 0,
            document_id,
        )
        if line_id and not line_id.startswith('new-'):
            db.execute_dict_query(
                """
                UPDATE document_line
                SET position = %s,
                    description = COALESCE(NULLIF(%s, ''), 'Discount line'),
                    sku = %s,
                    quantity = %s,
                    unit = %s,
                    unit_price_excl_tax = %s,
                    discount_rate = %s,
                    line_total_excl_tax = %s
                WHERE id = %s AND document_id = %s
                """,
                (
                    line.get('position'),
                    line.get('sku') or None,
                    line.get('sku') or None,
                    line.get('quantity') or 1,
                    line.get('unit') or 'U',
                    line.get('unit_price_excl_tax') or 0,
                    line.get('discount_rate') or 0,
                    line.get('line_total_excl_tax') or 0,
                    line_id,
                    document_id,
                ),
            )
        else:
            db.execute_dict_query(
                """
                INSERT INTO document_line (
                    document_id,
                    position,
                    description,
                    sku,
                    quantity,
                    unit,
                    unit_price_excl_tax,
                    discount_rate,
                    line_total_excl_tax
                )
                VALUES (%s, %s, COALESCE(NULLIF(%s, ''), 'Discount line'), %s, %s, %s, %s, %s, %s)
                """,
                (document_id, *params),
            )

    rows = db.execute_dict_query(
        """
        SELECT id,
               position,
               quantity,
               unit,
               unit_price_excl_tax,
               discount_rate,
               sku,
               line_total_excl_tax
        FROM document_line
        WHERE document_id = %s
        ORDER BY position ASC
        """,
        (document_id,),
    )
    return {'document_id': document_id, 'lines': rows}