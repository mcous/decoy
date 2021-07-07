"""Pytest plugin to setup and teardown a Decoy plugin."""
import pytest
from typing import Iterable
from decoy import Decoy


@pytest.fixture
def decoy() -> Iterable[Decoy]:
    """Get a Decoy test double container."""
    decoy = Decoy()
    yield decoy
    decoy.reset()
