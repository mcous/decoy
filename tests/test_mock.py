"""Smoke and acceptance tests for main Decoy interface."""

import inspect

import pytest

from decoy import Decoy, errors
from decoy.spy import AsyncSpy, Spy
from decoy.warnings import IncorrectCallWarning

from .fixtures import SomeClass, some_func


def test_create_mock(decoy: Decoy) -> None:
    """It creates a mock from a class."""
    subject = decoy.mock(cls=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass`>"


def test_method_noop(decoy: Decoy) -> None:
    """A method mock no-ops by default."""
    subject = decoy.mock(cls=SomeClass)
    result = subject.foo("hello")

    assert result is None


def test_decoy_creates_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a function."""
    subject = decoy.mock(func=some_func)

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(some_func)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_func`>"


def test_func_noop(decoy: Decoy) -> None:
    """A function mock no-ops by default."""
    subject = decoy.mock(func=some_func)
    result = subject("hello")

    assert result is None


def test_func_bad_call(decoy: Decoy) -> None:
    """It raises an IncorrectCallWarning if call is bad."""
    subject = decoy.mock(func=some_func)

    with pytest.warns(IncorrectCallWarning):
        subject("hello", "world")  # type: ignore[call-arg]


def test_decoy_creates_specless_spy(decoy: Decoy) -> None:
    """It should be able to create a spec-less spy."""
    subject = decoy.mock(name="subject")

    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `subject`>"


def test_decoy_creates_specless_async_spy(decoy: Decoy) -> None:
    """It should be able to create an async specless spy."""
    subject = decoy.mock(name="subject", is_async=True)

    assert isinstance(subject, AsyncSpy)


def test_decoy_mock_name_required(decoy: Decoy) -> None:
    """A name should be required for the mock."""
    with pytest.raises(errors.MockNameRequiredError):
        decoy.mock()  # type: ignore[call-overload]
