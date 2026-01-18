"""Smoke and acceptance tests for main Decoy interface."""

import inspect
import sys
from typing import Any

import pytest

from decoy import Decoy, errors
from decoy.spy import AsyncSpy, Spy
from decoy.warnings import IncorrectCallWarning

from . import fixtures


def test_create_mock(decoy: Decoy) -> None:
    """It creates a callable mock that no-ops."""
    subject = decoy.mock(name="alice")
    result = subject()

    assert result is None
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `alice`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.noop)


def test_create_mock_requires_name(decoy: Decoy) -> None:
    """It requires a name for a mock with no spec."""
    with pytest.raises(errors.MockNameRequiredError):
        decoy.mock()  # type:ignore[call-overload]


def test_child_mock(decoy: Decoy) -> None:
    """The attributes of a mock are also mocks."""
    parent = decoy.mock(name="alice")
    subject = parent.child
    result = subject()

    assert subject is parent.child
    assert result is None
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `alice.child`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.noop)


def test_attribute_set_and_delete(decoy: Decoy) -> None:
    """The caller may set attributes on a mock and delete them to reset them."""
    subject = decoy.mock(name="subject")

    subject.prop_name = 41
    assert subject.prop_name == 41

    del subject.prop_name
    assert isinstance(subject.prop_name, Spy)


async def test_create_async_mock(decoy: Decoy) -> None:
    """It creates an async callable mock that no-ops."""
    subject = decoy.mock(name="alice", is_async=True)
    result = await subject()

    assert result is None
    assert isinstance(subject, AsyncSpy)
    assert repr(subject) == "<Decoy mock `alice`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.noop)


def test_create_func_mock(decoy: Decoy) -> None:
    """It creates a mock based on a function."""
    subject = decoy.mock(func=fixtures.some_func)
    result = subject("hello")

    assert result is None
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_func`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.some_func)


async def test_create_async_func_mock(decoy: Decoy) -> None:
    """It creates a mock based on an async function."""
    subject = decoy.mock(func=fixtures.some_async_func)
    result = await subject("hello")

    assert result is None
    assert isinstance(subject, AsyncSpy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_async_func`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.some_async_func)


def test_create_decorated_func_mock(decoy: Decoy) -> None:
    """It creates a mock based on a decorated function."""
    subject = decoy.mock(func=fixtures.some_wrapped_func)
    result = subject("hello")

    assert result is None
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.some_wrapped_func`>"
    assert inspect.signature(subject) == inspect.signature(fixtures.some_func)


def test_create_callable_class_mock(decoy: Decoy) -> None:
    """It creates a mock based on a callable class."""
    subject = decoy.mock(cls=fixtures.SomeCallableClass)
    result = subject(123)

    def _expected_signature(val: int) -> int:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, fixtures.SomeCallableClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeCallableClass`>"
    assert inspect.signature(subject) == inspect.signature(_expected_signature)


async def test_create_async_callable_class_mock(decoy: Decoy) -> None:
    """It creates a mock based on an async callable class."""
    subject = decoy.mock(cls=fixtures.SomeAsyncCallableClass)
    result = await subject(123)

    def _expected_signature(val: int) -> int:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, fixtures.SomeAsyncCallableClass)
    assert isinstance(subject, AsyncSpy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeAsyncCallableClass`>"
    assert inspect.signature(subject) == inspect.signature(_expected_signature)


def test_create_class_mock(decoy: Decoy) -> None:
    """It creates a mock from a class spec."""
    subject = decoy.mock(cls=fixtures.SomeClass)

    assert isinstance(subject, fixtures.SomeClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass`>"


def test_create_generic_class_mock(decoy: Decoy) -> None:
    """It creates a mock from a generic class spec."""
    subject: fixtures.GenericClass[object] = decoy.mock(cls=fixtures.GenericClass)

    assert isinstance(subject, fixtures.GenericClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.GenericClass`>"


def test_create_concrete_generic_class_mock(decoy: Decoy) -> None:
    """It creates a mock from an alias to a concrete generic class spec."""
    subject = decoy.mock(cls=fixtures.ConcreteAlias)

    assert isinstance(subject, fixtures.GenericClass)
    assert isinstance(subject, Spy)
    assert repr(subject) == "<Decoy mock `tests.fixtures.GenericClass`>"


def test_create_method_mock(decoy: Decoy) -> None:
    """It creates a child mock from a class spec."""
    subject = decoy.mock(cls=fixtures.SomeClass).foo
    result = subject("hello")

    def _expected_signature(val: str) -> str:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.foo`>"


def test_create_staticmethod_mock(decoy: Decoy) -> None:
    """It creates a child staticmethod mock from a class spec."""
    subject = decoy.mock(cls=fixtures.SomeClass).static_method
    result = subject("hello")

    def _expected_signature(hello: str) -> int:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.static_method`>"


def test_create_classmethod_mock(decoy: Decoy) -> None:
    """It creates a child classmethod mock from a class spec."""
    subject = decoy.mock(cls=fixtures.SomeClass).class_method
    result = subject("hello")

    def _expected_signature(hello: str) -> int:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.class_method`>"


def test_create_decorated_method_mock(decoy: Decoy) -> None:
    """It creates a child mock of a decorated method from a class spec."""
    subject = decoy.mock(cls=fixtures.SomeClass).some_wrapped_method
    result = subject("hello")

    def _expected_signature(val: str) -> str:
        raise NotImplementedError()

    assert result is None
    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(_expected_signature)
    assert (
        repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.some_wrapped_method`>"
    )


def test_create_attribute_mock(decoy: Decoy) -> None:
    """It creates a child mock of a class's primitive attribute."""
    subject = decoy.mock(cls=fixtures.SomeClass).some_attr

    expected_signature = (
        inspect.signature(bool)
        if sys.version_info >= (3, 13)
        else inspect.signature(fixtures.noop)
    )

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == expected_signature
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.some_attr`>"


def test_create_attribute_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an attribute."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).child_attr

    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.SomeClass)


def test_create_attribute_type_alias_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from a type alias attribute."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).alias_attr

    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.GenericClass)


def test_create_property_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an property getter."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).child

    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.SomeClass)


def test_create_optional_property_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an property getter with Optional return."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).optional_child
    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.SomeClass)

    subject = decoy.mock(cls=fixtures.SomeNestedClass).union_child_and_none
    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.SomeClass)

    subject = decoy.mock(cls=fixtures.SomeNestedClass).union_none_and_child
    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.SomeClass)


def test_create_union_class_mock(decoy: Decoy) -> None:
    """A child class mock from an property with union return is not typed."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).union_child

    assert isinstance(subject, Spy)
    assert not isinstance(subject, fixtures.SomeClass)
    assert not isinstance(subject, fixtures.SomeAsyncClass)


def test_create_type_alias_class_mock(decoy: Decoy) -> None:
    """It creates a child class mock from an property getter with type alias return."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass).alias_child

    assert isinstance(subject, Spy)
    assert isinstance(subject, fixtures.GenericClass)


def test_create_untyped_property_mock(decoy: Decoy) -> None:
    """It creates a child mock of a class's property getter without a type."""
    subject = decoy.mock(cls=fixtures.SomeClass).mystery_property

    assert isinstance(subject, Spy)
    assert inspect.signature(subject) == inspect.signature(fixtures.noop)
    assert repr(subject) == "<Decoy mock `tests.fixtures.SomeClass.mystery_property`>"


def test_func_bad_call(decoy: Decoy) -> None:
    """It raises an IncorrectCallWarning if call is bad."""
    subject = decoy.mock(func=fixtures.some_func)

    with pytest.warns(IncorrectCallWarning):
        subject("hello", "world")  # type: ignore[call-arg]


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
def test_bad_type_hints(decoy: Decoy) -> None:
    """It tolerates bad type hints without failing at runtime."""

    class _BadTypeHints:
        not_ok: "None[Any]"  # pyright: ignore[reportInvalidTypeArguments]

    subject = decoy.mock(cls=_BadTypeHints).not_ok

    assert isinstance(subject, Spy)


def test_context_manager(decoy: Decoy) -> None:
    """It creates a context manager."""
    subject = decoy.mock(name="cm")

    with subject as result:
        assert result is None


async def test_async_context_manager(decoy: Decoy) -> None:
    """It creates an async context manager."""
    subject = decoy.mock(name="acm")

    async with subject as result:
        assert result is None
