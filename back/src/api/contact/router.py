from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .schemas import ContactCreate, ContactResponse, ContactUpdate
from src.repository.database.repository import DatabaseRepository

router = APIRouter()


def get_db():
    return DatabaseRepository()


@router.get("/api/contact", response_model=List[ContactResponse])
def list_contacts(db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT c.id, c.account_id, c.name, c.email, c.phone, c.role_title, c.created_at,
               a.name AS account_name
        FROM contact c
        LEFT JOIN account a ON a.id = c.account_id
        ORDER BY created_at DESC
        """
    )
    return rows


@router.get("/api/contact/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        SELECT c.id, c.account_id, c.name, c.email, c.phone, c.role_title, c.created_at,
               a.name AS account_name
        FROM contact c
        LEFT JOIN account a ON a.id = c.account_id
        WHERE c.id = %s
        """,
        (contact_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Contact not found")
    return rows[0]


@router.post("/api/contact", response_model=ContactResponse)
def create_contact(payload: ContactCreate, db=Depends(get_db)):
    rows = db.execute_dict_query(
        """
        INSERT INTO contact (account_id, name, email, phone, role_title)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, account_id, name, email, phone, role_title, created_at,
                  NULL::text AS account_name
        """,
        (payload.account_id, payload.name, payload.email, payload.phone, payload.role_title),
    )
    return rows[0]


@router.put("/api/contact/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: str, payload: ContactUpdate, db=Depends(get_db)):
    fields = []
    values = []

    for field in ["account_id", "name", "email", "phone", "role_title"]:
        value = getattr(payload, field)
        if value is not None:
            fields.append(f"{field} = %s")
            values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(contact_id)
    rows = db.execute_dict_query(
        f"""
        UPDATE contact
        SET {', '.join(fields)}
        WHERE id = %s
        RETURNING id, account_id, name, email, phone, role_title, created_at
        """,
        tuple(values),
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact = rows[0]
    if contact.get("account_id"):
        account_rows = db.execute_dict_query("SELECT name FROM account WHERE id = %s", (contact["account_id"],))
        contact["account_name"] = account_rows[0]["name"] if account_rows else None
    else:
        contact["account_name"] = None
    return contact


@router.delete("/api/contact/{contact_id}")
def delete_contact(contact_id: str, db=Depends(get_db)):
    rows = db.execute_dict_query(
        "DELETE FROM contact WHERE id = %s RETURNING id",
        (contact_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"id": rows[0]["id"]}
