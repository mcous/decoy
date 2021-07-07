"""Test fixtures."""
import pytest
from decoy import Decoy

pytest_plugins = ["pytester"]


@pytest.fixture
def decoy() -> Decoy:
    """Get a new instance of the Decoy state container.

    Warnings are disabled for more quiet tests.
    """
    return Decoy()
