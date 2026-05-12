"""Vector database filter building utilities for Qdrant."""

from typing import Optional, Dict
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range


def build_conditions(filters: Optional[Dict]) -> Optional[Filter]:
    """Build Qdrant filter conditions from simple dict filters.
    
    Args:
        filters: Dict with optional keys:
            - part_id, vendor, part_type, in_stock, tenant_id: exact match
            - price_min, price_max: range filters
    
    Returns:
        Qdrant Filter object or None
    """
    if not filters:
        return None
    
    conditions = []
    
    # Match filters (exact value)
    match_fields = ['part_id', 'vendor', 'part_type', 'in_stock', 'tenant_id']
    for field in match_fields:
        if field in filters:
            conditions.append(FieldCondition(
                key=field,
                match=MatchValue(value=filters[field])
            ))
    
    # Range filters for price
    if 'price_min' in filters:
        conditions.append(FieldCondition(
            key='price',
            range=Range(gte=filters['price_min'])
        ))
    if 'price_max' in filters:
        conditions.append(FieldCondition(
            key='price',
            range=Range(lte=filters['price_max'])
        ))
    
    return Filter(must=conditions) if conditions else None


def format_result(payload: Dict, score: Optional[float] = None) -> Dict:
    """Format Qdrant payload into human-readable result."""
    return {
        'id': payload.get('part_id'),
        'name': payload.get('part_name'),
        'type': payload.get('part_type'),
        'description': payload.get('description'),
        'price': f"${payload.get('price', 0):.2f}",
        'vendor': payload.get('vendor'),
        'in_stock': 'Yes' if payload.get('in_stock') else 'No',
        'tags': payload.get('tags', []),
        'score': score
    }
