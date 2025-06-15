"""Test fixtures."""

import pytest

from decoy.next import Decoy


@pytest.fixture()
def decoy() -> Decoy:
    """Create a Decoy instance for testing."""
    return Decoy()
