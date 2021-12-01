"""Tests for spy creation."""
import pytest
import inspect
from functools import partial
from typing import Any, NamedTuple

from decoy.warnings import IncorrectCallWarning
from decoy.spy_calls import SpyCall
from decoy.spy import create_spy, AsyncSpy, Spy, SpyConfig

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
    spy.child(four=4, five=5, six=6)
    spy(7, eight=8, nine=9)

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="decoy.spy.Spy", args=(1, 2, 3), kwargs={}),
        SpyCall(
            spy_id=id(spy.child),
            spy_name="child",
            args=(),
            kwargs={"four": 4, "five": 5, "six": 6},
        ),
        SpyCall(
            spy_id=id(spy),
            spy_name="decoy.spy.Spy",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
    ]


def test_create_spy_from_spec_function() -> None:
    """It should be able to create a test spy from a spec function."""
    calls = []

    spy = create_spy(SpyConfig(spec=some_func, handle_call=lambda c: calls.append(c)))

    spy("hello")
    spy(val="world")

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="some_func", args=("hello",), kwargs={}),
        SpyCall(spy_id=id(spy), spy_name="some_func", args=("world",), kwargs={}),
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

    await spy(val="1")
    await spy("6")

    assert calls == [
        SpyCall(spy_id=id(spy), spy_name="some_async_func", args=("1",), kwargs={}),
        SpyCall(spy_id=id(spy), spy_name="some_async_func", args=("6",), kwargs={}),
    ]


def test_create_spy_from_spec_class() -> None:
    """It should be able to create a test spy from a spec class."""
    calls = []

    spy = create_spy(SpyConfig(spec=SomeClass, handle_call=lambda c: calls.append(c)))

    spy.foo(val="1")
    spy.bar(a=4, b=5.0, c="6")
    spy.do_the_thing(flag=True)

    assert calls == [
        SpyCall(spy_id=id(spy.foo), spy_name="SomeClass.foo", args=("1",), kwargs={}),
        SpyCall(
            spy_id=id(spy.bar),
            spy_name="SomeClass.bar",
            args=(4, 5.0, "6"),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.do_the_thing),
            spy_name="SomeClass.do_the_thing",
            args=(),
            kwargs={"flag": True},
        ),
    ]


async def test_create_spy_from_async_spec_class() -> None:
    """It should be able to create a test spy from a class with async methods."""
    calls = []

    spy = create_spy(
        SpyConfig(spec=SomeAsyncClass, handle_call=lambda c: calls.append(c))
    )

    await spy.foo(val="1")
    await spy.bar(a=4, b=5.0, c="6")
    await spy.do_the_thing(flag=True)

    assert calls == [
        SpyCall(
            spy_id=id(spy.foo),
            spy_name="SomeAsyncClass.foo",
            args=("1",),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.bar),
            spy_name="SomeAsyncClass.bar",
            args=(4, 5.0, "6"),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.do_the_thing),
            spy_name="SomeAsyncClass.do_the_thing",
            args=(),
            kwargs={"flag": True},
        ),
    ]


def test_create_nested_spy() -> None:
    """It should be able to create a spy that goes several properties deep."""
    calls = []

    spy = create_spy(
        SpyConfig(spec=SomeNestedClass, handle_call=lambda c: calls.append(c))
    )

    spy.foo("1")
    spy.child.bar(a=4, b=5.0, c="6")
    spy.child.do_the_thing(flag=True)

    assert calls == [
        SpyCall(
            spy_id=id(spy.foo),
            spy_name="SomeNestedClass.foo",
            args=("1",),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.child.bar),
            spy_name="SomeNestedClass.child.bar",
            args=(4, 5.0, "6"),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy.child.do_the_thing),
            spy_name="SomeNestedClass.child.do_the_thing",
            args=(),
            kwargs={"flag": True},
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

    await spy._async_child.bar(a=4, b=5.0, c="6")
    spy._sync_child.do_the_thing(flag=True)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            spy_name="_SomeClass._async_child.bar",
            args=(4, 5.0, "6"),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            spy_name="_SomeClass._sync_child.do_the_thing",
            args=(),
            kwargs={"flag": True},
        ),
    ]


async def test_create_nested_spy_using_class_type_hints() -> None:
    """It should be able to dive using type hints on the class."""

    class _SomeClass:
        _async_child: SomeAsyncClass
        _sync_child: SomeClass

    calls = []
    spy = create_spy(SpyConfig(spec=_SomeClass, handle_call=lambda c: calls.append(c)))

    await spy._async_child.bar(a=4, b=5.0, c="6")
    spy._sync_child.do_the_thing(flag=False)

    assert calls == [
        SpyCall(
            spy_id=id(spy._async_child.bar),
            spy_name="_SomeClass._async_child.bar",
            args=(4, 5.0, "6"),
            kwargs={},
        ),
        SpyCall(
            spy_id=id(spy._sync_child.do_the_thing),
            spy_name="_SomeClass._sync_child.do_the_thing",
            args=(),
            kwargs={"flag": False},
        ),
    ]


@pytest.mark.filterwarnings("ignore:'NoneType' object is not subscriptable")
async def test_create_nested_spy_using_non_runtime_type_hints() -> None:
    """It should gracefully degrade if type hints cannot be resolved."""

    class _SomeClass:
        _property: "None[str]"

        async def _do_something_async(self) -> None:
            pass

    calls = []
    spy = create_spy(SpyConfig(spec=_SomeClass, handle_call=lambda c: calls.append(c)))
    spy._property.do_something(7, eight=8, nine=9)
    await spy._do_something_async()

    assert calls == [
        SpyCall(
            spy_id=id(spy._property.do_something),
            spy_name="_SomeClass._property.do_something",
            args=(7,),
            kwargs={"eight": 8, "nine": 9},
        ),
        SpyCall(
            spy_id=id(spy._do_something_async),
            spy_name="_SomeClass._do_something_async",
            args=(),
            kwargs={},
        ),
    ]


def test_warn_if_called_incorrectly() -> None:
    """It should trigger a warning if the spy is called incorrectly."""
    spy = create_spy(SpyConfig(spec=some_func, handle_call=noop))

    with pytest.warns(IncorrectCallWarning, match="missing a required argument"):
        spy(wrong_arg_name="1")


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
        sync_spy("hello"),
        await async_spy("from thr"),
        sync_spy("other"),
        await async_spy("side"),
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

    assert inspect.signature(spy) == inspect.Signature(
        parameters=(
            inspect.Parameter(
                name="args",
                annotation=Any,
                kind=inspect.Parameter.VAR_POSITIONAL,
            ),
            inspect.Parameter(
                name="kwargs",
                annotation=Any,
                kind=inspect.Parameter.VAR_KEYWORD,
            ),
        ),
        return_annotation=Any,
    )


def test_spy_matches_static_signature() -> None:
    """It should pass `inspect.signature` checks on static methods."""

    class _StaticClass:
        @staticmethod
        def foo(bar: int) -> float:
            raise NotImplementedError()

        @staticmethod
        async def bar(baz: str) -> float:
            raise NotImplementedError()

    class_spy = create_spy(SpyConfig(spec=_StaticClass, handle_call=noop))
    actual_instance = _StaticClass()

    assert inspect.signature(class_spy.foo) == inspect.signature(actual_instance.foo)
    assert inspect.signature(class_spy.bar) == inspect.signature(actual_instance.bar)
    assert isinstance(class_spy.foo, Spy)
    assert isinstance(class_spy.bar, AsyncSpy)


class SpyReprSpec(NamedTuple):
    """Spec data for BaseSpy.__repr__ tests."""

    config: SpyConfig
    expected: str


@pytest.mark.parametrize(
    SpyReprSpec._fields,
    [
        SpyReprSpec(
            config=SpyConfig(spec=SomeClass, handle_call=noop),
            expected="<Decoy mock of tests.common.SomeClass>",
        ),
        SpyReprSpec(
            config=SpyConfig(spec=some_func, handle_call=noop),
            expected="<Decoy mock of tests.common.some_func>",
        ),
        SpyReprSpec(
            config=SpyConfig(name="hello", handle_call=noop),
            expected='<Decoy mock "hello">',
        ),
        SpyReprSpec(
            config=SpyConfig(handle_call=noop),
            expected="<Decoy mock>",
        ),
        SpyReprSpec(
            config=SpyConfig(
                spec=partial(SomeClass.foo, None),
                name="SomeClass.foo",
                module_name="tests.common",
                handle_call=noop,
            ),
            expected="<Decoy mock of tests.common.SomeClass.foo>",
        ),
        SpyReprSpec(
            config=SpyConfig(
                spec=partial(SomeClass.foo, None),
                name="SomeClass.foo",
                handle_call=noop,
            ),
            expected="<Decoy mock of SomeClass.foo>",
        ),
    ],
)
def test_spy_repr(config: SpyConfig, expected: str) -> None:
    """It should have an informative repr."""
    subject = create_spy(config)
    result = repr(subject)

    assert result == expected
