import sys
from pathlib import Path

import pytest

from src.lib.denormalizers.denormalizer import Denormalizer

def test_get_groups_mapping():
    """Test get_groups_mapping returns correct mappings"""
    denormalizer = Denormalizer()
    
    # Build the full path to the test file
    test_file = Path(__file__).resolve().parents[4] / 'var' / 'storage' / 'ETIM-9.0-ALL-SECTORS-CSV-METRIC-EI-2022-12-05' / 'ETIMARTGROUP.csv'
    
    groups_map = denormalizer.get_groups_mapping(test_file, key='ARTGROUPID', target_field='GROUPDESC')
    
    assert isinstance(groups_map, dict)
    assert len(groups_map) > 0
    
    # Test specific mappings
    assert groups_map['EG000001'] == 'Cables'
    assert groups_map['EG010320'] == 'Lifting equipment'
    assert groups_map['EG020700'] == 'Building - Other'



