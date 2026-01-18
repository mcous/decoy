"""Tests for Decoy.when."""

import contextlib
import os
from typing import Any, AsyncGenerator, Generator, Optional

import pytest

from decoy import Decoy, errors
from decoy.warnings import IncorrectCallWarning, MiscalledStubWarning

from .. import fixtures


def test_when_then_return(decoy: Decoy) -> None:
    """It ca be configured to return a value."""
    subject = decoy.mock(name="subject")
    decoy.when(subject()).then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_then_raise(decoy: Decoy) -> None:
    """It can be configured to raise an exception."""
    subject = decoy.mock(name="subject")

    decoy.when(subject()).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject()


def test_when_then_do(decoy: Decoy) -> None:
    """It can be configured to run a function."""

    def _then_do_action() -> str:
        return "hello from the other side"

    subject = decoy.mock(name="subject")
    decoy.when(subject()).then_do(_then_do_action)

    result = subject()

    assert result == "hello from the other side"


def test_when_then_do_async_not_allowed(decoy: Decoy) -> None:
    """Raises error if async func passed to sync `then_do`."""
    subject = decoy.mock(name="subject")

    async def _async_action(arg: str) -> str:
        raise NotImplementedError()

    with pytest.raises(errors.MockNotAsyncError):
        decoy.when(subject()).then_do(_async_action)


def test_when_then_enter_with(decoy: Decoy) -> None:
    """It can be configured to return a context manager."""

    class _Spec:
        @contextlib.contextmanager
        def enter(self) -> Generator[int, None, None]:
            yield -1

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.enter()).then_enter_with(42)

    with subject.enter() as result:
        assert result == 42


async def test_when_then_return_async(decoy: Decoy) -> None:
    """It ca be configured to return a value from an async function."""
    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(await subject()).then_return("hello world")

    result = await subject()

    assert result == "hello world"


async def test_when_then_raise_async(decoy: Decoy) -> None:
    """It can be configured to raise an exception from an async function."""
    subject = decoy.mock(name="subject", is_async=True)

    decoy.when(await subject()).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        await subject()


async def test_when_then_do_async(decoy: Decoy) -> None:
    """It can be configured to run a function from an async function."""

    def _then_do_action() -> str:
        return "hello from the other side"

    async def _then_do_action_async() -> str:
        return "hello from the async side"

    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(await subject()).then_do(_then_do_action)
    result = await subject()
    assert result == "hello from the other side"

    decoy.when(await subject()).then_do(_then_do_action_async)
    result = await subject()
    assert result == "hello from the async side"


async def test_when_then_enter_with_async(decoy: Decoy) -> None:
    """It can be configured to return a context manager from an async function."""

    class _Spec:
        @contextlib.asynccontextmanager
        async def enter(self) -> AsyncGenerator[int, None]:
            yield -1

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.enter()).then_enter_with(42)

    async with subject.enter() as result:
        assert result == 42


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_miss(decoy: Decoy) -> None:
    """It noops if stubbing missing."""
    subject = decoy.mock(name="subject")
    decoy.when(subject("hello")).then_return("hello world")

    result = subject("goodbye")

    assert result is None


def test_when_reset(decoy: Decoy) -> None:
    """It removes stubbings on reset."""
    subject = decoy.mock(name="subject")
    decoy.when(subject()).then_return("hello world")
    decoy.reset()

    result = subject()

    assert result is None


def test_when_multiple_stubbings(decoy: Decoy) -> None:
    """It returns the latest stubbing."""
    subject = decoy.mock(name="subject")
    decoy.when(subject()).then_return("not ready yet")
    decoy.when(subject()).then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_with_args(decoy: Decoy) -> None:
    """It returns a value when called with args."""
    subject = decoy.mock(name="subject")

    decoy.when(subject()).then_return("no args")
    decoy.when(subject("hello", {"world": True})).then_return("hello world")

    result = subject("hello", {"world": True})

    assert result == "hello world"


def test_when_then_with_kwargs_in_stubbing(decoy: Decoy) -> None:
    """It binds args and kwargs in stub configuration."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    decoy.when(subject(a="hello", b=True)).then_return("hello world")

    result = subject("hello", b=True)

    assert result == "hello world"


def test_when_with_kwargs_in_call(decoy: Decoy) -> None:
    """It binds args and kwargs in call."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    decoy.when(subject("hello", b=True)).then_return("hello world")

    result = subject(a="hello", b=True)

    assert result == "hello world"


def test_when_no_mock(decoy: Decoy) -> None:
    """It raises an exception if called without a mock."""
    with pytest.raises(errors.MissingRehearsalError):
        decoy.when(fixtures.noop())


def test_when_no_mock_after_success(decoy: Decoy) -> None:
    """It raises an exception if no mock even if previous stubbing succeeded."""
    subject = decoy.mock(func=fixtures.some_func)

    decoy.when(subject("hello")).then_return("hello world")

    with pytest.raises(errors.MissingRehearsalError):
        decoy.when(fixtures.noop())


def test_when_signature_wrong_in_stubbing(decoy: Decoy) -> None:
    """It warns if stub config does not match signature."""
    subject = decoy.mock(func=fixtures.some_func)

    with pytest.warns(IncorrectCallWarning):
        decoy.when(subject("hello", "world"))  # type: ignore[call-arg]


def test_when_no_match_warning(decoy: Decoy) -> None:
    """It raises a MiscalledStubWarning if calls don't match stubbings."""
    subject = decoy.mock(name="subject")

    decoy.when(subject("hello")).then_return("hello world")

    subject("goodbye")

    with pytest.warns(MiscalledStubWarning) as warnings:
        decoy.reset()

    assert str(warnings[0].message) == os.linesep.join(
        [
            "Stub was called but no matching rehearsal found.",
            "Found 1 rehearsal:",
            "1.\tsubject('hello')",
            "Found 1 call:",
            "1.\tsubject('goodbye')",
        ]
    )


def test_when_ignore_extra_args(decoy: Decoy) -> None:
    """It can be configured ignore extra args in the call."""

    def _get_a_thing(id: str, default: Optional[int] = None) -> int:
        raise NotImplementedError()

    subject = decoy.mock(func=_get_a_thing)

    decoy.when(subject("some-id"), ignore_extra_args=True).then_return(42)

    result = subject("some-id", 101)
    assert result == 42


def test_when_then_return_multiple(decoy: Decoy) -> None:
    """It can figure multiple return values at once."""
    subject = decoy.mock(name="subject")
    decoy.when(subject("hello")).then_return("hola", "world")

    assert subject("hello") == "hola"
    assert subject("hello") == "world"
    assert subject("hello") == "world"


def test_context_manager_mock(decoy: Decoy) -> None:
    """Can stub the `__enter__` and `__exit__` methods."""
    is_exited = False

    def _on_exit(*args: Any, **kwargs: Any) -> None:
        nonlocal is_exited
        is_exited = True

    class _Spec:
        def __enter__(self) -> int:
            return -1

        def __exit__(self, *args: Any, **kwargs: Any) -> None:
            return None

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.__enter__()).then_return(42)
    decoy.when(subject.__exit__(None, None, None)).then_do(_on_exit)

    with subject as result:
        assert result == 42

    assert is_exited is True


async def test_async_context_manager_mock(decoy: Decoy) -> None:
    """Can stub the `__aenter__` and `__aexit__` methods."""
    is_exited = False

    async def _on_exit(*args: Any, **kwargs: Any) -> None:
        nonlocal is_exited
        is_exited = True

    class _Spec:
        async def __aenter__(self) -> int:
            return -1

        async def __aexit__(self, *args: Any, **kwargs: Any) -> Optional[bool]:
            return False

    subject = decoy.mock(cls=_Spec)

    decoy.when(await subject.__aenter__()).then_return(42)
    decoy.when(await subject.__aexit__(None, None, None)).then_do(_on_exit)

    async with subject as result:
        assert result == 42

    assert is_exited is True


def test_when_get_then_return(decoy: Decoy) -> None:
    """It can stub an attribute getter."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_return(42)

    assert subject.prop_name == 42


def then_when_get_then_return_multiple(decoy: Decoy) -> None:
    """It can stub an attribute getter with multiple returns."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_return(43, 44)

    assert subject.prop_name == 43
    assert subject.prop_name == 44
    assert subject.prop_name == 44


def test_when_get_then_raise(decoy: Decoy) -> None:
    """It can configure a getter to raise."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        _ = subject.prop_name


def test_when_get_then_do(decoy: Decoy) -> None:
    """It can configure a getter to side-effect."""

    def _handle_get(*args: Any, **kwargs: Any) -> int:
        return 84

    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).then_do(_handle_get)

    assert subject.prop_name == 84


def test_when_set_then_raise(decoy: Decoy) -> None:
    """It can configure a setter to raise."""
    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)

    decoy.when(prop_rehearser.set(42)).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject.prop_name = 42


def test_when_set_then_do(decoy: Decoy) -> None:
    """It can configure a setter to side-effect."""
    value = -1

    def _handle_set(next_value: int) -> None:
        nonlocal value
        value = next_value

    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)
    decoy.when(prop_rehearser.set(42)).then_do(_handle_set)

    subject.prop_name = 42

    assert value == 42


def test_when_delete_then_raise(decoy: Decoy) -> None:
    """It can configure a deleter to raise."""
    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)

    decoy.when(prop_rehearser.delete()).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        del subject.prop_name


def test_when_delete_then_do(decoy: Decoy) -> None:
    """It can configure a deleter to side-effect."""
    is_deleted = False

    def _handle_delete() -> None:
        nonlocal is_deleted
        is_deleted = True

    subject = decoy.mock(name="subject")
    prop_rehearser = decoy.prop(subject.prop_name)
    decoy.when(prop_rehearser.delete()).then_do(_handle_delete)

    del subject.prop_name

    assert is_deleted is True
