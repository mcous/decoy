"""Pytest plugin to setup and teardown a Decoy plugin."""
import pytest
from decoy import Decoy


@pytest.fixture
def decoy() -> Decoy:
    """Get a Decoy test double container."""
    return Decoy()
