from fastapi import APIRouter, Depends, HTTPException

from src.repository.database.repository import DatabaseRepository

router = APIRouter()


def get_db():
    return DatabaseRepository()


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


@router.get('/api/family/{family_id}')
def get_family(family_id: str, db=Depends(get_db)):
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
def create_family(payload: dict, db=Depends(get_db)):
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
def update_family(family_id: str, payload: dict, db=Depends(get_db)):
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
def delete_family(family_id: str, db=Depends(get_db)):
    db.execute_dict_query(
        'DELETE FROM product_family WHERE family_id = %s',
        (family_id,),
    )
    rows = db.execute_dict_query('DELETE FROM family WHERE id = %s RETURNING id', (family_id,))
    if not rows:
      raise HTTPException(status_code=404, detail='Family not found')
    return {'id': rows[0]['id']}