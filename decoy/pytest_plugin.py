"""Pytest plugin to setup and teardown a Decoy instance."""
import pytest
from typing import Iterable
from decoy import Decoy


@pytest.fixture
def decoy() -> Iterable[Decoy]:
    """Get a Decoy container and tear it down after the test."""
    decoy = Decoy()
    yield decoy
    decoy.reset()
