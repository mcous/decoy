"""Tests for the Decoy double creator."""
from mock import MagicMock, AsyncMock
from typing import Callable

from decoy import Decoy
from .common import SomeClass, SomeNestedClass, some_func


def test_decoy_creates_magicmock(decoy: Decoy) -> None:
    """It should be able to create a MagicMock from a class."""
    stub = decoy.create_decoy(spec=SomeClass)

    assert isinstance(stub, MagicMock)
    assert isinstance(stub, SomeClass)


def test_decoy_creates_nested_magicmock(decoy: Decoy) -> None:
    """It should be able to create a nested MagicMock from a class."""
    stub = decoy.create_decoy(spec=SomeNestedClass)

    assert isinstance(stub, MagicMock)
    assert isinstance(stub, SomeNestedClass)
    assert isinstance(stub.child, MagicMock)


def test_decoy_creates_asyncmock(decoy: Decoy) -> None:
    """It should be able to create an AsyncMock from a class."""
    stub = decoy.create_decoy(spec=SomeClass, is_async=True)

    assert isinstance(stub, AsyncMock)  # type: ignore[misc]
    assert isinstance(stub, SomeClass)


def test_decoy_creates_func_magicmock(decoy: Decoy) -> None:
    """It should be able to create a MagicMock from a function."""
    stub = decoy.create_decoy_func(spec=some_func, is_async=False)

    assert isinstance(stub, MagicMock)


def test_decoy_creates_func_asyncmock(decoy: Decoy) -> None:
    """It should be able to create an AsyncMock from a function."""
    stub = decoy.create_decoy_func(spec=some_func, is_async=True)

    assert isinstance(stub, AsyncMock)  # type: ignore[misc]


def test_decoy_creates_func_without_spec(decoy: Decoy) -> None:
    """It should be able to create a function without a spec."""
    stub: Callable[..., str] = decoy.create_decoy_func()

    assert isinstance(stub, MagicMock)


def test_decoy_functions_return_none(decoy: Decoy) -> None:
    """Decoy functions should return None by default."""
    stub = decoy.create_decoy_func(spec=some_func)

    assert stub("hello") is None


def test_decoy_methods_return_none(decoy: Decoy) -> None:
    """Decoy classes should return None by default."""
    stub = decoy.create_decoy(spec=SomeClass)

    assert stub.foo("hello") is None
    assert stub.bar(1, 2.0, "3") is None


def test_decoy_nested_methods_return_none(decoy: Decoy) -> None:
    """Decoy classes should return None by default."""
    stub = decoy.create_decoy(spec=SomeNestedClass)

    print(dir(SomeNestedClass))
    print(dir(stub))

    assert stub.foo("hello") is None
    assert stub.child.bar(1, 2.0, "3") is None
