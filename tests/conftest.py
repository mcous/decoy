"""Test fixtures."""
import pytest
from decoy import Decoy


@pytest.fixture
def decoy() -> Decoy:
    """Get a new instance of the Decoy state container."""
    return Decoy()
