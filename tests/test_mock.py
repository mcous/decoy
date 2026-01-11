"""Smoke and acceptance tests for main Decoy interface."""

import inspect
import sys
from typing import Any

import pytest

from decoy import Decoy, errors
from decoy.spy import AsyncSpy, Spy
from decoy.warnings import IncorrectCallWarning

from .fixtures import (
    SomeAsyncCallableClass,
    SomeAsyncClass,
    SomeCallableClass,
    SomeClass,
    SomeNestedClass,
    noop,
    some_async_func,
    some_func,
)


def test_create_mock(decoy: Decoy) -> None:
    """It creates a mock from a class spec."""
    subject = decoy.mock(cls=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass`>"


def test_create_method_mock(decoy: Decoy) -> None:
    """It creates a child mock from a class spec."""
    subject = decoy.mock(cls=SomeClass).foo

    def _expected_signature(val: str) -> str:
        raise NotImplementedError()

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.foo`>"


def test_method_noop(decoy: Decoy) -> None:
    """A method mock no-ops by default."""
    subject = decoy.mock(cls=SomeClass)
    result = subject.foo("hello")

    assert result is None


def test_create_staticmethod_mock(decoy: Decoy) -> None:
    """It creates a child staticmethod mock from a class spec."""
    subject = decoy.mock(cls=SomeClass).static_method

    def _expected_signature(hello: str) -> int:
        raise NotImplementedError()

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.static_method`>"


def test_create_classmethod_mock(decoy: Decoy) -> None:
    """It creates a child classmethod mock from a class spec."""
    subject = decoy.mock(cls=SomeClass).class_method

    def _expected_signature(hello: str) -> int:
        raise NotImplementedError()

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.class_method`>"


def test_create_decorated_method_mock(decoy: Decoy) -> None:
    """It creates a child mock of a decorated method from a class spec."""
    subject = decoy.mock(cls=SomeClass).some_wrapped_method

    def _expected_signature(val: str) -> str:
        raise NotImplementedError()

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert (
        repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.some_wrapped_method`>"
    )


def test_create_attribute_mock(decoy: Decoy) -> None:
    """It creates a child mock of an attribute."""
    subject = decoy.mock(cls=SomeClass).some_attr

    expected_signature = (
        inspect.signature(bool)
        if sys.version_info >= (3, 13)
        else inspect.signature(noop)
    )

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == expected_signature
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.some_attr`>"


def test_create_attribute_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an attribute."""
    subject = decoy.mock(cls=SomeNestedClass).child_attr

    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeClass)


def test_create_property_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an property getter."""
    subject = decoy.mock(cls=SomeNestedClass).child

    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeClass)


def test_create_optional_property_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an property getter with Optional return."""
    subject = decoy.mock(cls=SomeNestedClass).optional_child
    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeClass)

    subject = decoy.mock(cls=SomeNestedClass).union_child_and_none
    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeClass)

    subject = decoy.mock(cls=SomeNestedClass).union_none_and_child
    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeClass)


def test_create_union_class_mock(decoy: Decoy) -> None:
    """A child class mock from an property with union return is not typed."""
    subject = decoy.mock(cls=SomeNestedClass).union_child

    assert isinstance(subject, Spy)
    assert not isinstance(subject, SomeClass)
    assert not isinstance(subject, SomeAsyncClass)


def test_create_callable_mock(decoy: Decoy) -> None:
    """It creates a mock from a callable class."""
    subject = decoy.mock(cls=SomeCallableClass)

    def _expected_signature(val: int) -> int:
        raise NotImplementedError()

    assert isinstance(subject, Spy)
    assert isinstance(subject, SomeCallableClass)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)


def test_create_async_callable_mock(decoy: Decoy) -> None:
    """It creates a mock from an async callable class."""
    subject = decoy.mock(cls=SomeAsyncCallableClass)

    async def _expected_signature(val: int) -> int:
        raise NotImplementedError()

    assert isinstance(subject, AsyncSpy)
    assert isinstance(subject, SomeAsyncCallableClass)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert inspect.iscoroutinefunction(subject.__call__)


def test_create_func_mock(decoy: Decoy) -> None:
    """It creates a mock from a function spec."""
    subject = decoy.mock(func=some_func)

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(some_func)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_func`>"


def test_func_noop(decoy: Decoy) -> None:
    """A function mock no-ops by default."""
    subject = decoy.mock(func=some_func)
    result = subject("hello")

    assert result is None


def test_create_async_func_mock(decoy: Decoy) -> None:
    """It creates a mock from an async function spec."""
    subject = decoy.mock(func=some_async_func)

    assert isinstance(subject, AsyncSpy)
    assert inspect.signature(subject) == inspect.signature(some_async_func)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_async_func`>"


async def test_async_func_noop(decoy: Decoy) -> None:
    """An async function mock no-ops by default."""
    subject = decoy.mock(func=some_async_func)
    result = await subject("hello")

    assert result is None


def test_func_bad_call(decoy: Decoy) -> None:
    """It raises an IncorrectCallWarning if call is bad."""
    subject = decoy.mock(func=some_func)

    with pytest.warns(IncorrectCallWarning):
        subject("hello", "world")  # type: ignore[call-arg]


def test_create_specless_mock(decoy: Decoy) -> None:
    """It creates a mock without a spec."""
    subject = decoy.mock(name="subject")

    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `subject`>"


def test_create_specless_async_mock(decoy: Decoy) -> None:
    """It creates an async mock without a spec."""
    subject = decoy.mock(name="subject", is_async=True)

    assert isinstance(subject, AsyncSpy)
    assert inspect.iscoroutinefunction(subject.__call__)


async def test_async_specless_mock_noop(decoy: Decoy) -> None:
    """An async specless mock no-ops by default."""
    subject = decoy.mock(name="subject", is_async=True)
    result = await subject("hello")

    assert result is None


def test_mock_name_required(decoy: Decoy) -> None:
    """A name is required for a mock without a spec."""
    with pytest.raises(errors.MockNameRequiredError):
        decoy.mock()  # type: ignore[call-overload]


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
def test_bad_type_hints(decoy: Decoy) -> None:
    """It tolerates bad type hints without failing at runtime."""

    class _BadTypeHints:
        not_ok: "None[Any]"  # pyright: ignore[reportInvalidTypeArguments]

    subject = decoy.mock(cls=_BadTypeHints).not_ok

    assert isinstance(subject, Spy)
