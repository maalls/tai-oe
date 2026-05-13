"""
Global pytest fixtures for unit tests
"""
import sys
import importlib
import pkgutil
from pathlib import Path

# Add project root to path so `src` package is importable
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Compatibility aliases: keep old test imports (`domain.*`, `infrastructure.*`, ...)
# pointing to the same module objects as `src.*` to avoid enum/class identity splits.
_ALIASES = ("domain", "infrastructure", "repository", "service")
for _name in _ALIASES:
    src_module = importlib.import_module(f"src.{_name}")
    sys.modules.setdefault(_name, src_module)

    if hasattr(src_module, "__path__"):
        prefix = f"src.{_name}."
        for module_info in pkgutil.walk_packages(src_module.__path__, prefix=prefix):
            src_submodule_name = module_info.name
            src_submodule = importlib.import_module(src_submodule_name)
            alias_name = src_submodule_name.replace("src.", "", 1)
            sys.modules.setdefault(alias_name, src_submodule)

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
