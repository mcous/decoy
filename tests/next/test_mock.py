"""Tests for creating mocks."""

import inspect

import pytest

from decoy.next import Decoy, errors

from .. import fixtures


def test_create_mock(decoy: Decoy) -> None:
    """It creates a callable mock that no-ops."""
    subject = decoy.mock(name="alice")
    result = subject()

    assert result is None
    assert repr(subject) == "<Decoy mock 'alice'>"


def test_create_mock_requires_name(decoy: Decoy) -> None:
    """It creates a callable mock that no-ops."""
    with pytest.raises(errors.MockNameRequiredError):
        decoy.mock()  # type:ignore[call-overload]


async def test_create_async_mock(decoy: Decoy) -> None:
    """It creates an async callable mock that no-ops."""
    subject = decoy.mock(name="alice", is_async=True)
    result = await subject()

    assert result is None
    assert repr(subject) == "<Decoy mock 'alice'>"


def test_create_func_mock(decoy: Decoy) -> None:
    """It creates a mock based on a function."""
    subject = decoy.mock(func=fixtures.some_func)
    result = subject("hello")

    assert result is None
    assert repr(subject) == "<Decoy mock 'tests.fixtures.some_func'>"


def test_func_signature(decoy: Decoy) -> None:
    """It passes signature checks."""
    spec = fixtures.some_func
    expected = inspect.signature(spec)
    subject = decoy.mock(func=spec)
    result = inspect.signature(subject)

    assert result == expected


async def test_create_async_func_mock(decoy: Decoy) -> None:
    """It creates a mock based on an async function."""
    subject = decoy.mock(func=fixtures.some_async_func)
    result = await subject("hello")

    assert result is None


def test_create_callable_class_mock(decoy: Decoy) -> None:
    """It creates a mock based on a callable class."""
    subject = decoy.mock(cls=fixtures.SomeCallableClass)
    result = subject(123)

    assert result is None


async def test_create_async_callable_class_mock(decoy: Decoy) -> None:
    """It creates a mock based on an async callable class."""
    subject = decoy.mock(cls=fixtures.SomeAsyncCallableClass)
    result = await subject(123)

    assert result is None


def test_create_class_mock(decoy: Decoy) -> None:
    """It creates a mock class instance."""
    subject = decoy.mock(cls=fixtures.SomeClass)

    assert isinstance(subject, fixtures.SomeClass)


def test_class_mock_method_signature(decoy: Decoy) -> None:
    """It creates a mock class instance."""
    spec = fixtures.SomeClass
    expected = inspect.signature(spec().foo)
    subject = decoy.mock(cls=fixtures.SomeClass)
    result = inspect.signature(subject.foo)

    assert result == expected


def test_class_mock_staticmethod_signature(decoy: Decoy) -> None:
    """It creates a mock class instance."""
    spec = fixtures.SomeClass
    expected = inspect.signature(spec.static_method)
    subject = decoy.mock(cls=fixtures.SomeClass)
    result = inspect.signature(subject.static_method)

    assert result == expected


def test_class_mock_classmethod_signature(decoy: Decoy) -> None:
    """It creates a mock class instance."""
    spec = fixtures.SomeClass
    expected = inspect.signature(spec.class_method)
    subject = decoy.mock(cls=fixtures.SomeClass)
    result = inspect.signature(subject.class_method)

    assert result == expected


def test_create_child_mock_from_attr(decoy: Decoy) -> None:
    """It creates a child with the correct spec for an attribute."""
    parent = decoy.mock(cls=fixtures.SomeNestedClass)
    subject = parent.child_attr

    assert isinstance(subject, fixtures.SomeClass)


def test_create_child_mock_is_cached(decoy: Decoy) -> None:
    """It re-uses mock children that get created."""
    parent = decoy.mock(cls=fixtures.SomeNestedClass)

    assert parent.child_attr is parent.child_attr


def test_create_child_mock_from_property(decoy: Decoy) -> None:
    """It creates a child with the correct spec for an attribute."""
    parent = decoy.mock(cls=fixtures.SomeNestedClass)
    subject = parent.child

    assert isinstance(subject, fixtures.SomeClass)


def test_create_child_mock_from_optional(decoy: Decoy) -> None:
    """It creates child mocks from optional properties."""
    subject = decoy.mock(cls=fixtures.SomeNestedClass)

    assert isinstance(subject.optional_child, fixtures.SomeClass)
    assert isinstance(subject.union_none_child, fixtures.SomeClass)
    assert not isinstance(subject.union_child, fixtures.SomeClass)
    assert not isinstance(subject.union_child, fixtures.SomeAsyncClass)
