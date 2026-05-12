"""Fabdis brand handling utilities."""

from __future__ import annotations
from typing import Optional, Sequence, Mapping, Any


def handle_brand(
    marque: str,
    conn,
) -> Mapping[str, Any]:
    
    print("handling brand for marque:", marque)
    brand = {"id": None, "marque": marque}

    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM brand WHERE LOWER(marque) = LOWER(%s) LIMIT 1",
            (marque,),
        )
        row = cursor.fetchone()
        if row:
            brand = {"id": row[0], "marque": marque}
        else:
            cursor.execute(
                "INSERT INTO brand (name, marque, created_at, updated_at) VALUES (%s, %s, now(), now()) RETURNING id",
                (marque, marque),
            )
            row = cursor.fetchone()
            if row:
                brand = {"id": row[0], "marque": marque}
            else:
                raise ValueError(f"Failed to insert brand for marque: {marque}")
            conn.commit()
    
    print(f"Handling brand for marque: {marque} -> {brand['id']}")
    return brand