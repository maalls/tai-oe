from fastapi import APIRouter, Depends, HTTPException
from .schemas import AccountResponse, AccountCreate, AccountUpdate
from src.repository.database.repository import DatabaseRepository
from typing import List

router = APIRouter()

def get_db():
    return DatabaseRepository()

@router.get("/api/account", response_model=List[AccountResponse])
def list_accounts(db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vat_number, siret, address_line1, address_line2,
               postal_code, city, country_code, payment_terms_default,
               phone, website, industry, created_at, updated_at
        FROM account
        ORDER BY created_at DESC
        """
    )
    return rows

@router.get("/api/account/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT id, name, vat_number, siret, address_line1, address_line2,
               postal_code, city, country_code, payment_terms_default,
               phone, website, industry, created_at, updated_at
        FROM account
        WHERE id = %s
        """,
        (account_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    return rows[0]

@router.post("/api/account", response_model=AccountResponse)
def create_account(payload: AccountCreate, db=Depends(get_db)):
    row = db.execute_dict_query(
        """
        INSERT INTO account (
            name, vat_number, siret, address_line1, address_line2,
            postal_code, city, country_code, payment_terms_default,
            phone, website, industry
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, name, vat_number, siret, address_line1, address_line2,
                  postal_code, city, country_code, payment_terms_default,
                  phone, website, industry, created_at, updated_at
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
            payload.phone,
            payload.website,
            payload.industry,
        ),
    )
    return row[0]

@router.put("/api/account/{account_id}", response_model=AccountResponse)
def update_account(account_id: str, payload: AccountUpdate, db=Depends(get_db)):
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
        'phone',
        'website',
        'industry',
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
                  phone, website, industry, created_at, updated_at
        """,
        tuple(values)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return row[0]

@router.delete("/api/account/{account_id}")
def delete_account(account_id: str, db=Depends(get_db)):
    row = db.execute_dict_query(
        "DELETE FROM account WHERE id = %s RETURNING id",
        (account_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"id": row[0]["id"]}
