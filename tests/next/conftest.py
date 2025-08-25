"""Test fixtures."""

from typing import Generator

import pytest

from decoy.next import Decoy


@pytest.fixture()
def decoy() -> Generator[Decoy, None, None]:
    """Create a Decoy instance for testing."""
    with Decoy.create() as decoy:
        yield decoy
