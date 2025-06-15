"""Tests for module-level imports of Decoy methods."""
import pytest
import decoy
from decoy.spy import Spy

from .fixtures import (
    SomeClass,
    some_func,
    some_async_func,
)

def test_decoy_creates_spy() -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.mock(cls=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)


def test_decoy_creates_func_spy() -> None:
    """It should be able to create a Spy from a function."""
    subject = decoy.mock(func=some_func)

    assert isinstance(subject, Spy)


def test_decoy_creates_specless_spy() -> None:
    """It should be able to create a spec-less spy."""
    subject = decoy.mock(name="subject")

    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `subject`>"

@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_then_return() -> None:
    """It should be able to configure a stub return with a rehearsal."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject).called_with("hello").then_return("hello world")

    result = subject(val="hello")
    assert result == "hello world"

    result = subject(val="hello")
    assert result == "hello world"

    result = subject("asdfghjkl")
    assert result is None

@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_then_return_class() -> None:
    """It should be able to configure a stub return with a rehearsal."""
    subject = decoy.mock(cls=SomeClass)

    decoy.when(subject.foo).called_with("hello").then_return("hello world")

    result = subject.foo(val="hello")
    assert result == "hello world"

    result = subject.foo(val="hello")
    assert result == "hello world"

    result = subject.foo("asdfghjkl")
    assert result is None

async def test_when_then_return_async() -> None:
    """It should be able to configure a stub action with a rehearsal."""
    subject = decoy.mock(func=some_async_func)

    decoy.when(subject).called_with("what's up").then_return("not much")

    result = await subject("what's up")
    assert result == "not much"
