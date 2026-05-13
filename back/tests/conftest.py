"""
Global pytest fixtures for unit tests
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from tests.fixtures.fake_repositories import FakeEmailRepository
from tests.fixtures.sample_data import sample_email


@pytest.fixture
def fake_email_repo():
    """Provides a fresh FakeEmailRepository for each test"""
    return FakeEmailRepository()


@pytest.fixture
def sample_unclassified_email():
    """Provides a sample unclassified email"""
    return sample_email(id="test-1")


@pytest.fixture
def sample_classified_email():
    """Provides a sample classified email"""
    return sample_email(id="test-2", classification="quote")
