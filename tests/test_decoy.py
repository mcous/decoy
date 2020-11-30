"""Tests for the Decoy double creator."""
from decoy import Decoy
from decoy.spy import Spy

from .common import SomeClass, some_func


def test_decoy_creates_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    stub = decoy.create_decoy(spec=SomeClass)

    assert isinstance(stub, SomeClass)


def test_decoy_creates_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    stub = decoy.create_decoy_func(spec=some_func)

    assert isinstance(stub, Spy)
