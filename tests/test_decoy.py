"""Smoke and acceptance tests for main Decoy interface."""
import pytest
from decoy import Decoy, errors
from decoy.spy import Spy, AsyncSpy
from typing import Optional

from .common import SomeClass, SomeAsyncClass, some_func


def test_decoy_creates_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.mock(cls=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)

    # test deprecated create_decoy method
    subject = decoy.create_decoy(spec=SomeClass)

    assert isinstance(subject, SomeClass)
    assert isinstance(subject, Spy)


def test_decoy_creates_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.mock(func=some_func)

    assert isinstance(subject, Spy)

    # test deprecated create_decoy_func method
    subject = decoy.create_decoy_func(spec=some_func)

    assert isinstance(subject, Spy)


def test_decoy_creates_async_func_spy(decoy: Decoy) -> None:
    """It should be able to create a Spy from a class."""
    subject = decoy.mock(is_async=True)

    assert isinstance(subject, AsyncSpy)

    # test deprecated create_decoy_func method
    subject = decoy.create_decoy_func(is_async=True)

    assert isinstance(subject, AsyncSpy)


@pytest.mark.filterwarnings("ignore::decoy.warnings.MiscalledStubWarning")
def test_when_then_return(decoy: Decoy) -> None:
    """It should be able to configure a stub return with a rehearsal."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject("hello")).then_return("hello world")

    result = subject("hello")
    assert result == "hello world"

    result = subject("asdfghjkl")
    assert result is None


def test_when_then_raise(decoy: Decoy) -> None:
    """It should be able to configure a stub raise with a rehearsal."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject("goodbye")).then_raise(ValueError("oh no"))

    with pytest.raises(ValueError, match="oh no"):
        subject("goodbye")


def test_when_then_do(decoy: Decoy) -> None:
    """It should be able to configure a stub action with a rehearsal."""
    subject = decoy.mock(func=some_func)
    action_result = None

    def _then_do_action(arg: str) -> str:
        nonlocal action_result
        action_result = arg
        return "hello from the other side"

    decoy.when(subject("what's up")).then_do(_then_do_action)

    result = subject("what's up")
    assert action_result == "what's up"
    assert result == "hello from the other side"


def test_when_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: Optional[int] = None) -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    decoy.when(subject("some-id"), ignore_extra_args=True).then_return(42)

    result = subject("some-id", 101)
    assert result == 42


def test_verify(decoy: Decoy) -> None:
    """It should be able to configure a verification with a rehearsal."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"))

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("goodbye"))


def test_verify_times(decoy: Decoy) -> None:
    """It should be able to verify a call count."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"), times=1)
    decoy.verify(subject("goodbye"), times=0)

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("hello"), times=0)

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject("hello"), times=2)


def test_verify_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: Optional[int] = None) -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    subject("some-id", 101)

    decoy.verify(
        subject("some-id"),
        ignore_extra_args=True,
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject("wrong-id"),
            ignore_extra_args=True,
        )


@pytest.mark.asyncio
async def test_when_async(decoy: Decoy) -> None:
    """It should be able to stub an async method."""
    subject = decoy.mock(cls=SomeAsyncClass)

    decoy.when(await subject.foo("hello")).then_return("world")
    decoy.when(await subject.bar(0, 1.0, "2")).then_raise(ValueError("oh no"))

    assert await subject.foo("hello") == "world"

    with pytest.raises(ValueError, match="oh no"):
        await subject.bar(0, 1.0, "2")


@pytest.mark.asyncio
async def test_verify_async(decoy: Decoy) -> None:
    """It should be able to configure a verification with an async rehearsal."""
    subject = decoy.mock(cls=SomeAsyncClass)

    await subject.foo("hello")

    decoy.verify(await subject.foo("hello"))

    with pytest.raises(AssertionError):
        decoy.verify(await subject.foo("goodbye"))


def test_reset(decoy: Decoy) -> None:
    """It should be able to reset its state."""
    subject = decoy.mock(cls=SomeClass)

    subject.foo("hello")
    decoy.reset()

    with pytest.raises(AssertionError):
        decoy.verify(subject.foo("hello"))
