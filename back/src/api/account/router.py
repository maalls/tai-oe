from fastapi import APIRouter, Depends, HTTPException
from .schemas import AccountResponse, AccountCreate, AccountUpdate
from src.api.dependencies import get_database_repository
from src.repository.repository import DatabaseRepository
from typing import List

router = APIRouter()

@router.get("/api/account", response_model=List[AccountResponse])
def list_accounts(db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vat_number, siret, address_line1, address_line2,
               postal_code, city, country_code, payment_terms_default,
               NULL::text AS phone,
               NULL::text AS website,
               NULL::text AS industry,
               created_at, updated_at
        FROM account
        ORDER BY created_at DESC
        """
    )
    return rows

@router.get("/api/account/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vat_number, siret, address_line1, address_line2,
               postal_code, city, country_code, payment_terms_default,
               NULL::text AS phone,
               NULL::text AS website,
               NULL::text AS industry,
               created_at, updated_at
        FROM account
        WHERE id = %s
        """,
        (account_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    return rows[0]

@router.post("/api/account", response_model=AccountResponse)
def create_account(payload: AccountCreate, db: DatabaseRepository = Depends(get_database_repository)):
    row = db.execute_dict_query(
        """
        INSERT INTO account (
            name, vat_number, siret, address_line1, address_line2,
            postal_code, city, country_code, payment_terms_default
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, vat_number, siret, address_line1, address_line2,
                  postal_code, city, country_code, payment_terms_default,
                  NULL::text AS phone,
                  NULL::text AS website,
                  NULL::text AS industry,
                  created_at, updated_at
        """,
        (
            payload.name,
            payload.vat_number,
            payload.siret,
            payload.address_line1,
            payload.address_line2,
            payload.postal_code,
            payload.city,
            payload.country_code,
            payload.payment_terms_default,
        ),
    )
    return row[0]

@router.put("/api/account/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    payload: AccountUpdate,
    db: DatabaseRepository = Depends(get_database_repository),
):
    fields = []
    values = []
    for field in [
        'name',
        'vat_number',
        'siret',
        'address_line1',
        'address_line2',
        'postal_code',
        'city',
        'country_code',
        'payment_terms_default',
    ]:
        value = getattr(payload, field)
        if value is not None:
            fields.append(f"{field} = %s")
            values.append(value)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    values.append(account_id)
    row = db.execute_dict_query(
        f"""
        UPDATE account
        SET {', '.join(fields)}, updated_at = now()
        WHERE id = %s
        RETURNING id, name, vat_number, siret, address_line1, address_line2,
                  postal_code, city, country_code, payment_terms_default,
                  NULL::text AS phone,
                  NULL::text AS website,
                  NULL::text AS industry,
                  created_at, updated_at
        """,
        tuple(values)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return row[0]

@router.delete("/api/account/{account_id}")
def delete_account(account_id: str, db: DatabaseRepository = Depends(get_database_repository)):
    row = db.execute_dict_query(
        "DELETE FROM account WHERE id = %s RETURNING id",
        (account_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"id": row[0]["id"]}
