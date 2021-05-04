"""Test fixtures."""
import pytest
from decoy import Decoy


@pytest.fixture
def decoy() -> Decoy:
    """Get a new instance of the Decoy state container.

    Warnings are disabled for more quiet tests.
    """
    return Decoy(warn_on_missing_stubs=False)


@pytest.fixture
def strict_decoy() -> Decoy:
    """Get a new instance of the Decoy state container.

    Warnings are left in the default enabled state. Use this fixture
    to test warning behavior.
    """
    return Decoy()
