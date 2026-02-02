"""Tests for Decoy.when."""

from __future__ import annotations

import collections.abc
import contextlib
import os
import sys
from typing import Any

import pytest

from decoy import errors, warnings

from . import fixtures

if sys.version_info >= (3, 10):
    from decoy.next import Decoy

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


@pytest.fixture()
def decoy() -> collections.abc.Iterator[Decoy]:
    """Create a Decoy instance for testing."""
    with Decoy.create() as decoy:
        yield decoy


def test_when_then_return(decoy: Decoy) -> None:
    """It returns a value."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_then_raise(decoy: Decoy) -> None:
    """It raises an exception."""
    subject = decoy.mock(name="subject")

    decoy.when(subject).called_with().then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject()


def test_when_then_do(decoy: Decoy) -> None:
    """It runs a function."""

    def _then_do_action() -> str:
        return "hello from the other side"

    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_do(_then_do_action)

    result = subject()

    assert result == "hello from the other side"


def test_when_then_do_not_callable(decoy: Decoy) -> None:
    """Raises error if non-function passed to `then_do`."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.ThenDoActionNotCallableError, match="must be callable"):
        decoy.when(subject).called_with().then_do(42)  # type: ignore[arg-type]


def test_when_then_do_async_not_allowed(decoy: Decoy) -> None:
    """Raises an error if an async func is passed to sync `then_do`."""
    subject = decoy.mock(name="subject")

    async def _async_action(arg: str) -> str:
        return ""

    with pytest.raises(
        errors.MockNotAsyncError, match="cannot use an asynchronous callable"
    ):
        decoy.when(subject).called_with().then_do(_async_action)


def test_when_then_enter_with(decoy: Decoy) -> None:
    """It returns a context manager."""

    class _Spec:
        @contextlib.contextmanager
        def enter(self) -> collections.abc.Iterator[int]:
            yield -1

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.enter).called_with().then_enter_with(42)

    with subject.enter() as result:
        assert result == 42


async def test_when_then_return_async(decoy: Decoy) -> None:
    """It returns a value from an async function."""
    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(subject).called_with().then_return("hello world")

    result = await subject()

    assert result == "hello world"


async def test_when_then_raise_async(decoy: Decoy) -> None:
    """It raises an exception from an async function."""
    subject = decoy.mock(name="subject", is_async=True)

    decoy.when(subject).called_with().then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        await subject()


async def test_when_then_do_async(decoy: Decoy) -> None:
    """It runs a function from an async function."""

    def _then_do_action() -> str:
        return "hello from the other side"

    async def _then_do_action_async() -> str:
        return "hello from the async side"

    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(subject).called_with().then_do(_then_do_action)
    result = await subject()
    assert result == "hello from the other side"

    decoy.when(subject).called_with().then_do(_then_do_action_async)
    result = await subject()
    assert result == "hello from the async side"


async def test_when_then_enter_with_async(decoy: Decoy) -> None:
    """It returns a context manager from an async function."""

    class _Spec:
        @contextlib.asynccontextmanager
        async def enter(self) -> collections.abc.AsyncIterator[int]:
            yield -1

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.enter).called_with().then_enter_with(42)

    async with subject.enter() as result:
        assert result == 42


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_miss(decoy: Decoy) -> None:
    """It noops if stubbing is missing."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("hello world")

    result = subject("goodbye")

    assert result is None


def test_when_reset(decoy: Decoy) -> None:
    """It removes stubbings on reset."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("hello world")
    decoy.reset()

    result = subject()

    assert result is None


def test_when_multiple_stubbings(decoy: Decoy) -> None:
    """It returns the latest stubbing."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("not ready yet")
    decoy.when(subject).called_with().then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_with_args(decoy: Decoy) -> None:
    """It returns a value when called with args."""
    subject = decoy.mock(name="subject")

    decoy.when(subject).called_with().then_return("no args")
    decoy.when(subject).called_with("hello", {"world": True}).then_return("hello world")

    result = subject("hello", {"world": True})

    assert result == "hello world"


def test_when_then_with_kwargs_in_stubbing(decoy: Decoy) -> None:
    """It binds args and kwargs in the stub configuration."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    decoy.when(subject).called_with(a="hello", b=True).then_return("hello world")

    result = subject("hello", b=True)

    assert result == "hello world"


def test_when_with_kwargs_in_call(decoy: Decoy) -> None:
    """It binds args and kwargs in the call."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    decoy.when(subject).called_with("hello", b=True).then_return("hello world")

    result = subject(a="hello", b=True)

    assert result == "hello world"


def test_when_no_mock(decoy: Decoy) -> None:
    """It raises an exception if called without a mock."""
    with pytest.raises(errors.NotAMockError):
        decoy.when(fixtures.noop)


def test_when_signature_wrong_in_stubbing(decoy: Decoy) -> None:
    """It warns if stub config does not match signature."""
    subject = decoy.mock(func=fixtures.some_func)

    with pytest.raises(errors.SignatureMismatchError):
        decoy.when(subject).called_with("hello", "world")  # type: ignore[call-arg]


def test_when_no_match_warning(decoy: Decoy) -> None:
    """It raises a MiscalledStubWarning if calls don't match stubbings."""
    subject = decoy.mock(name="subject")

    decoy.when(subject).called_with("hello").then_return("hello world")

    with pytest.warns(warnings.MiscalledStubWarning) as warnings_log:
        subject("goodbye")

    assert str(warnings_log[0].message) == os.linesep.join(
        [
            "Stub was called but no matching rehearsal found.",
            "Found 1 rehearsal:",
            "1.\tsubject('hello')",
            "Found 1 call:",
            "1.\tsubject('goodbye')",
        ]
    )


def test_when_ignore_extra_args(decoy: Decoy) -> None:
    """It ignores extra args in the call."""

    def _get_a_thing(id: str, default: int | None = None) -> int:
        raise NotImplementedError()

    subject = decoy.mock(func=_get_a_thing)

    decoy.when(subject, ignore_extra_args=True).called_with("some-id").then_return(42)

    result = subject("some-id", 101)
    assert result == 42


def test_when_ignore_extra_args_signature(decoy: Decoy) -> None:
    """It does not raise a signature mismatch error when ignore_extra_args is set."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    decoy.when(subject, ignore_extra_args=True).called_with(a="hello")  # type: ignore[call-arg]

    with pytest.raises(errors.SignatureMismatchError):
        decoy.when(subject).called_with(not_a="hello")  # type: ignore[call-arg]


def test_when_times(decoy: Decoy) -> None:
    """It returns a value a given number of times."""
    subject = decoy.mock(name="subject")
    decoy.when(subject, times=2).called_with("hello").then_return("world")

    assert subject("hello") == "world"
    assert subject("hello") == "world"
    assert subject("hello") is None


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_entered(decoy: Decoy) -> None:
    """It limits matches to while the context manager is entered."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("world")
    decoy.when(subject, is_entered=False).called_with("hola").then_return("mundo")
    decoy.when(subject, is_entered=True).called_with("hei").then_return("verden")

    result_not_entered = [subject("hello"), subject("hola"), subject("hei")]

    with subject:
        result_entered = [subject("hello"), subject("hola"), subject("hei")]

    assert result_not_entered == ["world", "mundo", None]
    assert result_entered == ["world", None, "verden"]


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
async def test_when_async_entered(decoy: Decoy) -> None:
    """It limits matches to while the context manager is entered asynchronously."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("world")
    decoy.when(subject, is_entered=False).called_with("hola").then_return("mundo")
    decoy.when(subject, is_entered=True).called_with("hei").then_return("verden")

    result_not_entered = [subject("hello"), subject("hola"), subject("hei")]

    async with subject:
        result_entered = [subject("hello"), subject("hola"), subject("hei")]

    assert result_not_entered == ["world", "mundo", None]
    assert result_entered == ["world", None, "verden"]


def test_when_then_return_multiple(decoy: Decoy) -> None:
    """It returns a sequence of values."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("hola", "world")

    assert subject("hello") == "hola"
    assert subject("hello") == "world"
    assert subject("hello") == "world"


def test_context_manager_mock(decoy: Decoy) -> None:
    """Mocks the `__enter__` and `__exit__` methods."""
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

    decoy.when(subject.__enter__).called_with().then_return(42)
    decoy.when(subject.__exit__).called_with(None, None, None).then_do(_on_exit)

    with subject as result:
        assert result == 42

    assert is_exited is True


async def test_async_context_manager_mock(decoy: Decoy) -> None:
    """Mocks the `__aenter__` and `__aexit__` methods."""
    is_exited = False

    async def _on_exit(*args: Any, **kwargs: Any) -> None:
        nonlocal is_exited
        is_exited = True

    class _Spec:
        async def __aenter__(self) -> int:
            return -1

        async def __aexit__(self, *args: Any, **kwargs: Any) -> bool | None:
            return False

    subject = decoy.mock(cls=_Spec)

    decoy.when(subject.__aenter__).called_with().then_return(42)
    decoy.when(subject.__aexit__).called_with(None, None, None).then_do(_on_exit)

    async with subject as result:
        assert result == 42

    assert is_exited is True


def test_when_get_then_return(decoy: Decoy) -> None:
    """It mocks an attribute getter."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).get().then_return(42)

    assert subject.prop_name == 42


def then_when_get_then_return_multiple(decoy: Decoy) -> None:
    """It mocks an attribute getter with a sequence of returns."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).get().then_return(43, 44)

    assert subject.prop_name == 43
    assert subject.prop_name == 44
    assert subject.prop_name == 44


def test_when_get_then_raise(decoy: Decoy) -> None:
    """It raises from a getter."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).get().then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        _ = subject.prop_name


def test_when_get_then_do(decoy: Decoy) -> None:
    """It side-effects from a getter."""

    def _handle_get(*args: Any, **kwargs: Any) -> int:
        return 84

    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).get().then_do(_handle_get)

    assert subject.prop_name == 84


def test_when_get_after_stubbing(decoy: Decoy) -> None:
    """It mocks an attribute getter more than once."""
    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).get().then_return(42)
    decoy.when(subject.other_prop_name).get().then_return(63)
    decoy.when(subject.prop_name).get().then_return(84)

    assert subject.prop_name == 84


def test_when_set_then_raise(decoy: Decoy) -> None:
    """It raises from a setter."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).set(42).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject.prop_name = 42


def test_when_set_then_do(decoy: Decoy) -> None:
    """It side-effects from a setter."""
    value = -1

    def _handle_set(next_value: int) -> None:
        nonlocal value
        value = next_value

    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).set(42).then_do(_handle_set)

    subject.prop_name = 42

    assert value == 42


def test_when_delete_then_raise(decoy: Decoy) -> None:
    """It raises from a deleter."""
    subject = decoy.mock(name="subject")

    decoy.when(subject.prop_name).delete().then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        del subject.prop_name


def test_when_delete_then_do(decoy: Decoy) -> None:
    """It side-effects from a deleter."""
    is_deleted = False

    def _handle_delete() -> None:
        nonlocal is_deleted
        is_deleted = True

    subject = decoy.mock(name="subject")
    decoy.when(subject.prop_name).delete().then_do(_handle_delete)

    del subject.prop_name

    assert is_deleted is True
