"""Qdrant filter building utilities."""

from typing import Dict, Optional

try:
    from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
except ImportError:
    raise ImportError("Missing dependency: qdrant-client. Install with: pip install qdrant-client")


def build_filter(filters: Dict) -> Optional[Filter]:
    """Build Qdrant filter from simple dictionary.
    
    Args:
        filters: Dict with field filters, e.g.:
            {
                'field_name': 'value',  # exact match
                'price_min': 100,       # range >=
                'price_max': 500,       # range <=
            }
    
    Returns:
        Qdrant Filter object or None
    """
    if not filters:
        return None
    
    conditions = []
    
    # Handle exact matches for any field except range fields
    range_suffixes = ['_min', '_max', '_gt', '_gte', '_lt', '_lte']
    for key, value in filters.items():
        # Skip range filters (handled separately)
        if any(key.endswith(suffix) for suffix in range_suffixes):
            continue
        
        conditions.append(FieldCondition(
            key=key,
            match=MatchValue(value=value)
        ))
    
    # Handle range filters
    # Pattern: field_min/field_max or field_gte/field_lte
    range_fields = {}
    for key, value in filters.items():
        if key.endswith('_min') or key.endswith('_gte'):
            field = key.replace('_min', '').replace('_gte', '')
            if field not in range_fields:
                range_fields[field] = {}
            range_fields[field]['gte'] = value
        elif key.endswith('_max') or key.endswith('_lte'):
            field = key.replace('_max', '').replace('_lte', '')
            if field not in range_fields:
                range_fields[field] = {}
            range_fields[field]['lte'] = value
        elif key.endswith('_gt'):
            field = key.replace('_gt', '')
            if field not in range_fields:
                range_fields[field] = {}
            range_fields[field]['gt'] = value
        elif key.endswith('_lt'):
            field = key.replace('_lt', '')
            if field not in range_fields:
                range_fields[field] = {}
            range_fields[field]['lt'] = value
    
    for field, bounds in range_fields.items():
        conditions.append(FieldCondition(
            key=field,
            range=Range(**bounds)
        ))
    
    return Filter(must=conditions) if conditions else None
