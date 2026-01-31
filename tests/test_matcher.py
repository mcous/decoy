"""Matcher tests."""

from __future__ import annotations

import collections.abc
import dataclasses
import sys
from typing import NamedTuple

if sys.version_info >= (3, 13):
    from typing import TypeIs
else:
    from typing_extensions import TypeIs

import pytest

from decoy import errors

from . import fixtures

if sys.version_info >= (3, 10):
    from decoy.next import Decoy, Matcher

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


@pytest.fixture()
def decoy() -> collections.abc.Iterator[Decoy]:
    """Create a Decoy instance for testing."""
    with Decoy.create() as decoy:
        yield decoy


def _is_str(target: object) -> TypeIs[str]:
    return isinstance(target, str)


def test_matcher() -> None:
    """It matches based on a TypeIs function."""
    subject = Matcher(_is_str)

    assert "hello" == subject
    assert 42 != subject
    assert str(subject) == "<Matcher._is_str>"


def test_matcher_inspect() -> None:
    """It matches based on a built-in inspection functions."""
    subject = Matcher(callable)

    assert fixtures.some_func == subject
    assert 42 != subject
    assert str(subject) == "<Matcher.callable>"


def test_matcher_lambda() -> None:
    """It matches based on a lambda function."""
    subject = Matcher(lambda x: isinstance(x, int) and x % 2 == 0, name="is_even")

    assert 2 == subject
    assert 1 != subject
    assert str(subject) == "<Matcher.is_even>"


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_matcher_arg(decoy: Decoy) -> None:
    """It matches when used in called_with."""
    subject = decoy.mock(cls=fixtures.SomeClass)

    decoy.when(subject.foo).called_with(Matcher(_is_str).arg).then_return("yay")

    assert subject.foo("hello") == "yay"
    assert subject.foo(42) is None  # type: ignore[arg-type]


def test_matcher_capture() -> None:
    """It captures matching values."""
    subject = Matcher(_is_str)

    assert "hello" == subject
    assert subject.value == "hello"
    assert subject.values == ["hello"]

    assert "world" == subject
    assert subject.value == "world"
    assert subject.values == ["hello", "world"]


def test_matcher_no_capture() -> None:
    """It throws an error if no captured value."""
    subject = Matcher(_is_str)

    with pytest.raises(errors.NoMatcherValueCapturedError, match="has not matched"):
        _ = subject.value

    assert 42 != subject

    with pytest.raises(errors.NoMatcherValueCapturedError):
        _ = subject.value


def test_any() -> None:
    """It matches everything including None."""
    subject = Matcher.any()

    assert "hello" == subject
    assert None == subject  # noqa: E711
    assert str(subject) == "<Matcher.any>"


def test_something() -> None:
    """It matches everything except None."""
    subject = Matcher.something()

    assert "hello" == subject
    assert None != subject  # noqa: E711
    assert str(subject) == "<Matcher.something>"


def test_is_a() -> None:
    """It matches an isinstance check."""
    subject = Matcher.is_a(str)

    assert "hello" == subject
    assert 42 != subject
    assert str(subject) == "<Matcher.is_a str>"


def test_is_a_decoy(decoy: Decoy) -> None:
    """It matches an isinstance check on a decoy mock."""
    subject = Matcher.is_a(fixtures.SomeClass)

    assert decoy.mock(cls=fixtures.SomeClass) == subject


def test_is_a_with_attributes() -> None:
    """It matches an instance and partial attributes."""

    @dataclasses.dataclass
    class _Target:
        hello: str

    subject = Matcher.is_a(_Target, {"hello": "world"})

    assert _Target(hello="world") == subject
    assert _Target(hello="goodbye") != subject
    assert str(subject) == "<Matcher.is_a _Target {'hello': 'world'}>"


def test_is_not() -> None:
    """It negates a match."""
    subject = Matcher.is_not("hello")

    assert "hello" != subject
    assert "goodbye" == subject
    assert str(subject) == "<Matcher.is_not 'hello'>"


def test_has_attrs() -> None:
    """It matches against a partial set of attributes."""

    @dataclasses.dataclass
    class _TargetClass:
        hello: str

    class _TargetTuple(NamedTuple):
        hello: str

    subject = Matcher.has_attrs({"hello": "world"})

    assert _TargetClass(hello="world") == subject
    assert _TargetClass(hello="goodbye") != subject
    assert _TargetTuple(hello="world") == subject
    assert _TargetTuple(hello="goodbye") != subject
    assert str(subject) == "<Matcher.has_attrs {'hello': 'world'}>"


def test_dict_containing() -> None:
    """It matches a dict containing the given values."""
    subject = Matcher.dict_containing({"hello": "world", 42: True})

    assert {"hello": "world", 42: True} == subject
    assert {"hello": "world", "hola": "mundo", 42: True} == subject
    assert {} != subject
    assert {"hello": "world"} != subject
    assert {42: True} != subject
    assert "hello" != subject
    assert str(subject) == "<Matcher.dict_containing {'hello': 'world', 42: True}>"


def test_list_containing() -> None:
    """It matches a list containing the given values."""
    subject = Matcher.list_containing([1, 2, 3])

    assert [1, 2, 3] == subject
    assert [0, 1, 2, 3, 4] == subject
    assert [3, 2, 1] == subject
    assert [1, 2] != subject
    assert 1 != subject
    assert str(subject) == "<Matcher.list_containing [1, 2, 3]>"


def test_list_containing_in_order() -> None:
    """It matches a list containing the given values."""
    subject = Matcher.list_containing([1, 2], in_order=True)

    assert [1, 2] == subject
    assert [0, 1, 2, 3] == subject
    assert [1, 3, 2] == subject
    assert [2, 1] != subject
    assert 1 != subject

    assert str(subject) == "<Matcher.list_containing [1, 2] in_order=True>"


def test_string() -> None:
    """It matches strings by regex."""
    subject = Matcher.string("ello$")

    assert "hello" == subject
    assert "hello!" != subject
    assert 42 != subject
    assert str(subject) == "<Matcher.string 'ello$'>"


def test_error_type() -> None:
    """It matches an exception type."""
    subject = Matcher.error(RuntimeError)

    assert RuntimeError("oh no") == subject
    assert TypeError("oh no") != subject
    assert "oh no" != subject
    assert str(subject) == "<Matcher.error RuntimeError>"


def test_error_type_and_message() -> None:
    """It matches an exception type and message."""
    subject = Matcher.error(RuntimeError, message="^oh")

    assert RuntimeError("oh no") == subject
    assert RuntimeError("oh canada") == subject
    assert TypeError("oh no") != subject
    assert str(subject) == "<Matcher.error RuntimeError '^oh'>"
