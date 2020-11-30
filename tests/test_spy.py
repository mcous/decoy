"""Tests for spy creation."""
import pytest

from typing import Any
from decoy.spy import create_spy, AsyncSpy, SpyCall

from .common import (
    some_func,
    some_async_func,
    SomeClass,
    SomeAsyncClass,
    SomeNestedClass,
)

pytestmark = pytest.mark.asyncio


def test_create_spy() -> None:
    """It should be able to create a test spy."""
    calls = []

    spy = create_spy(handle_call=lambda c: calls.append(c))

    spy(1, 2, 3)
    spy(four=4, five=5, six=6)
    spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), args=(1, 2, 3), kwargs={}),
        SpyCall(spy_id=id(spy), args=(), kwargs={"four": 4, "five": 5, "six": 6}),
        SpyCall(spy_id=id(spy), args=(7,), kwargs={"eight": 8, "nine": 9}),
    ]


def test_create_spy_from_spec_function() -> None:
    """It should be able to create a test spy from a spec function."""
    calls = []

    spy = create_spy(spec=some_func, handle_call=lambda c: calls.append(c))

    spy(1, 2, 3)
    spy(four=4, five=5, six=6)
    spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), args=(1, 2, 3), kwargs={}),
        SpyCall(spy_id=id(spy), args=(), kwargs={"four": 4, "five": 5, "six": 6}),
        SpyCall(spy_id=id(spy), args=(7,), kwargs={"eight": 8, "nine": 9}),
    ]


async def test_create_spy_from_async_spec_function() -> None:
    """It should be able to create a test spy from an async function."""
    calls = []

    spy: AsyncSpy = create_spy(
        spec=some_async_func, handle_call=lambda c: calls.append(c)
    )

    await spy(1, 2, 3)
    await spy(four=4, five=5, six=6)
    await spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), args=(1, 2, 3), kwargs={}),
        SpyCall(spy_id=id(spy), args=(), kwargs={"four": 4, "five": 5, "six": 6}),
        SpyCall(spy_id=id(spy), args=(7,), kwargs={"eight": 8, "nine": 9}),
    ]


def test_create_spy_from_spec_class() -> None:
    """It should be able to create a test spy from a spec class."""
    calls = []

    spy = create_spy(spec=SomeClass, handle_call=lambda c: calls.append(c))

    spy.foo(1, 2, 3)
    spy.bar(four=4, five=5, six=6)
    spy.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy.foo), args=(1, 2, 3), kwargs={}),
        SpyCall(spy_id=id(spy.bar), args=(), kwargs={"four": 4, "five": 5, "six": 6}),
        SpyCall(spy_id=id(spy.do_the_thing), args=(7,), kwargs={"eight": 8, "nine": 9}),
    ]


async def test_create_spy_from_async_spec_class() -> None:
    """It should be able to create a test spy from a class with async methods."""
    calls = []

    spy = create_spy(spec=SomeAsyncClass, handle_call=lambda c: calls.append(c))

    await spy.foo(1, 2, 3)
    await spy.bar(four=4, five=5, six=6)
    await spy.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy.foo), args=(1, 2, 3), kwargs={}),
        SpyCall(spy_id=id(spy.bar), args=(), kwargs={"four": 4, "five": 5, "six": 6}),
        SpyCall(spy_id=id(spy.do_the_thing), args=(7,), kwargs={"eight": 8, "nine": 9}),
    ]


def test_create_nested_spy() -> None:
    """It should be able to create a spy that goes several properties deep."""
    calls = []

    spy = create_spy(spec=SomeNestedClass, handle_call=lambda c: calls.append(c))

    spy.foo(1, 2, 3)
    spy.child.bar(four=4, five=5, six=6)
    spy.child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy.foo), args=(1, 2, 3), kwargs={}),
        SpyCall(
            spy_id=id(spy.child.bar),
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy.child.do_the_thing),
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


async def test_create_nested_spy_using_property_type_hints() -> None:
    """It should be able to dive using type hints on @property getters."""

    class _SomeClass:
        @property
        def _async_child(self) -> SomeAsyncClass:
            ...

        @property
        def _sync_child(self) -> SomeClass:
            ...

    calls = []
    spy = create_spy(spec=_SomeClass, handle_call=lambda c: calls.append(c))

    await spy._async_child.bar(four=4, five=5, six=6)
    spy._sync_child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


async def test_create_nested_spy_using_class_type_hints() -> None:
    """It should be able to dive using type hints on the class."""

    class _SomeClass:
        _async_child: SomeAsyncClass
        _sync_child: SomeClass

    calls = []
    spy = create_spy(spec=_SomeClass, handle_call=lambda c: calls.append(c))

    await spy._async_child.bar(four=4, five=5, six=6)
    spy._sync_child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


async def test_spy_returns_handler_value() -> None:
    """The spy should return the value from its call handler when called."""
    call_count = 0

    def _handle_call(call: Any) -> int:
        nonlocal call_count
        call_count = call_count + 1
        return call_count

    sync_spy = create_spy(spec=some_func, handle_call=_handle_call)
    async_spy = create_spy(spec=some_async_func, handle_call=_handle_call)

    assert [
        sync_spy(),
        await async_spy(),
        sync_spy(),
        await async_spy(),
    ] == [1, 2, 3, 4]
