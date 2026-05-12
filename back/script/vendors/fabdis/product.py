"""Fabdis product handling utilities."""

from __future__ import annotations

from typing import Optional, Mapping, Any
from brand import handle_brand


def handle_product(
  data: Mapping[str, Any],
  conn
) -> None:
  
  print(
        f"Handling product for={data.get('REFCIALE')} "
        f"marque={data.get('MARQUE')} "
        f"name={data.get('LIBELLE40')} "
    )
  
  marque = data.get("MARQUE")
  if not marque:
    raise ValueError("Product is missing 'MARQUE' field, cannot handle brand")

  brand = handle_brand(marque, conn)
  
  product = {
      "sku": data.get("REFCIALE"),
      "name": data.get("LIBELLE40"),
      "brand": brand,
  }

  print(product)

  return product
  
  

