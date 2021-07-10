"""Tests for spy creation."""
import pytest
import inspect
from typing import Any

from decoy.spy import create_spy, AsyncSpy, SpyConfig, SpyCall

from .common import (
    noop,
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

    spy = create_spy(SpyConfig(handle_call=lambda c: calls.append(c)))

    spy(1, 2, 3)
    spy(four=4, five=5, six=6)
    spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="spy", args=(1, 2, 3), kwargs={}),
        SpyCall(
            spy_id=id(spy),
            spy_name="spy",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy), spy_name="spy", args=(7,), kwargs={"eight": 8, "nine": 9}
        ),
    ]


def test_create_spy_from_spec_function() -> None:
    """It should be able to create a test spy from a spec function."""
    calls = []

    spy = create_spy(SpyConfig(spec=some_func, handle_call=lambda c: calls.append(c)))

    spy(1, 2, 3)
    spy(four=4, five=5, six=6)
    spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="some_func", args=(1, 2, 3), kwargs={}),
        SpyCall(
            spy_id=id(spy),
            spy_name="some_func",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy),
            spy_name="some_func",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


async def test_create_spy_from_async_spec_function() -> None:
    """It should be able to create a test spy from an async function."""
    calls = []

    spy: AsyncSpy = create_spy(
        SpyConfig(
            spec=some_async_func,
            handle_call=lambda c: calls.append(c),
        )
    )

    await spy(1, 2, 3)
    await spy(four=4, five=5, six=6)
    await spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="some_async_func", args=(1, 2, 3), kwargs={}),
        SpyCall(
            spy_id=id(spy),
            spy_name="some_async_func",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy),
            spy_name="some_async_func",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


def test_create_spy_from_spec_class() -> None:
    """It should be able to create a test spy from a spec class."""
    calls = []

    spy = create_spy(SpyConfig(spec=SomeClass, handle_call=lambda c: calls.append(c)))

    spy.foo(1, 2, 3)
    spy.bar(four=4, five=5, six=6)
    spy.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy.foo), spy_name="SomeClass.foo", args=(1, 2, 3), kwargs={}
        ),
        SpyCall(
            spy_id=id(spy.bar),
            spy_name="SomeClass.bar",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy.do_the_thing),
            spy_name="SomeClass.do_the_thing",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


async def test_create_spy_from_async_spec_class() -> None:
    """It should be able to create a test spy from a class with async methods."""
    calls = []

    spy = create_spy(
        SpyConfig(spec=SomeAsyncClass, handle_call=lambda c: calls.append(c))
    )

    await spy.foo(1, 2, 3)
    await spy.bar(four=4, five=5, six=6)
    await spy.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy.foo), spy_name="SomeAsyncClass.foo", args=(1, 2, 3), kwargs={}
        ),
        SpyCall(
            spy_id=id(spy.bar),
            spy_name="SomeAsyncClass.bar",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy.do_the_thing),
            spy_name="SomeAsyncClass.do_the_thing",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


def test_create_nested_spy() -> None:
    """It should be able to create a spy that goes several properties deep."""
    calls = []

    spy = create_spy(
        SpyConfig(spec=SomeNestedClass, handle_call=lambda c: calls.append(c))
    )

    spy.foo(1, 2, 3)
    spy.child.bar(four=4, five=5, six=6)
    spy.child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy.foo),
            spy_name="SomeNestedClass.foo",
            args=(1, 2, 3),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.child.bar),
            spy_name="SomeNestedClass.child.bar",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy.child.do_the_thing),
            spy_name="SomeNestedClass.child.do_the_thing",
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
    spy = create_spy(SpyConfig(spec=_SomeClass, handle_call=lambda c: calls.append(c)))

    await spy._async_child.bar(four=4, five=5, six=6)
    spy._sync_child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            spy_name="_SomeClass._async_child.bar",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            spy_name="_SomeClass._sync_child.do_the_thing",
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
    spy = create_spy(SpyConfig(spec=_SomeClass, handle_call=lambda c: calls.append(c)))

    await spy._async_child.bar(four=4, five=5, six=6)
    spy._sync_child.do_the_thing(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            spy_name="_SomeClass._async_child.bar",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            spy_name="_SomeClass._sync_child.do_the_thing",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
async def test_create_nested_spy_using_non_runtime_type_hints() -> None:
    """It should gracefully degrade if type hints cannot be resolved."""

    class _SomeClass:
        _property: "None[str]"

    calls = []
    spy = create_spy(SpyConfig(spec=_SomeClass, handle_call=lambda c: calls.append(c)))
    spy._property.do_something(7, eight=8, nine=9)

    assert calls == [
        SpyCall(
            spy_id=id(spy._property.do_something),
            spy_name="_SomeClass._property.do_something",
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

    sync_spy = create_spy(SpyConfig(spec=some_func, handle_call=_handle_call))
    async_spy = create_spy(SpyConfig(spec=some_async_func, handle_call=_handle_call))

    assert [
        sync_spy(),
        await async_spy(),
        sync_spy(),
        await async_spy(),
    ] == [1, 2, 3, 4]


def test_spy_passes_instance_of() -> None:
    """A spy should pass instanceof checks."""
    spy = create_spy(SpyConfig(spec=SomeClass, handle_call=noop))

    assert isinstance(spy, SomeClass)


def test_spy_matches_signature() -> None:
    """It should pass `inspect.signature` checks."""
    class_spy = create_spy(SpyConfig(spec=SomeClass, handle_call=noop))
    actual_instance = SomeClass()
    assert inspect.signature(class_spy) == inspect.signature(SomeClass)
    assert inspect.signature(class_spy.foo) == inspect.signature(actual_instance.foo)
    assert inspect.signature(class_spy.bar) == inspect.signature(actual_instance.bar)
    assert inspect.signature(class_spy.do_the_thing) == inspect.signature(
        actual_instance.do_the_thing
    )

    func_spy = create_spy(SpyConfig(spec=some_func, handle_call=noop))
    assert inspect.signature(func_spy) == inspect.signature(some_func)

    spy = create_spy(SpyConfig(handle_call=noop))
    assert inspect.signature(spy) == inspect.signature(noop)


def test_spy_repr() -> None:
    """It should have an informative repr."""
    class_spy = create_spy(SpyConfig(spec=SomeClass, handle_call=noop))
    func_spy = create_spy(SpyConfig(spec=some_func, handle_call=noop))
    spy = create_spy(SpyConfig(handle_call=noop))

    assert repr(class_spy) == "<Decoy mock of tests.common.SomeClass>"
    assert repr(class_spy.foo) == "<Decoy mock of tests.common.SomeClass.foo>"
    assert repr(func_spy) == "<Decoy mock of tests.common.some_func>"
    assert repr(spy) == "<Decoy spy function>"
