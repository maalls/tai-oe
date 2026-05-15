import sys
from pathlib import Path

import pytest

from src.lib.importers.etim import Denormalizer


def test_denormalize():
    """Test that denormalize returns array of size 2"""
    denormalizer = Denormalizer()
    result = denormalizer.denormalize()
    assert isinstance(result, list)
    assert len(result) == 5554
    
    first = result[0]
    print(first)
