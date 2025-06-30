"""Tests for Decoy.when."""

import pytest

from decoy.next import Decoy, errors

from ..fixtures import some_func


def test_when_not_mock(decoy: Decoy) -> None:
    """It raises an exception if passed not a mock."""
    with pytest.raises(errors.NotAMockError):
        decoy.when(some_func)


def test_when_then_return_no_args(decoy: Decoy) -> None:
    """It returns a value with no args."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_reset(decoy: Decoy) -> None:
    """It removes stubbings on reset."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("hello world")
    decoy.reset()

    result = subject()

    assert result is None


def test_when_multiple_stubbings(decoy: Decoy) -> None:
    """It returns a value with no args."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("not ready yet")
    decoy.when(subject).called_with().then_return("hello world")

    result = subject()

    assert result == "hello world"


def test_when_then_return_args(decoy: Decoy) -> None:
    """It returns a value with args."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with().then_return("no args")
    decoy.when(subject).called_with("hello", 1, {"world": True}).then_return(
        "hello world"
    )

    result = subject("hello", 1, {"world": True})

    assert result == "hello world"


async def test_when_then_return_async(decoy: Decoy) -> None:
    """It returns a value with no args."""
    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(subject).called_with().then_return("hello world")

    result = await subject()

    assert result == "hello world"


def test_when_then_return_times(decoy: Decoy) -> None:
    """It returns a value a given number of times."""
    subject = decoy.mock(name="subject")
    decoy.when(subject, times=1).called_with("hello").then_return("world")

    subject("hello")
    result = subject("hello")

    assert result is None


def test_when_then_return_ignoring_extra_args(decoy: Decoy) -> None:
    """It returns a value with args."""
    subject = decoy.mock(name="subject")
    decoy.when(subject, ignore_extra_args=True).called_with("hello").then_return(
        "hello world"
    )

    result = subject("hello", "there")

    assert result == "hello world"


def test_when_then_return_multiple(decoy: Decoy) -> None:
    """It returns a value with args."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("hola", "world")

    results = [subject("hello"), subject("hello"), subject("hello")]

    assert results == ["hola", "world", "world"]


def test_when_then_raise(decoy: Decoy) -> None:
    """It raises an error."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_raise(Exception("oh no"))

    with pytest.raises(match="oh no"):
        subject("hello")


def test_when_then_do(decoy: Decoy) -> None:
    """It calls a function."""

    def _action(val: str) -> str:
        return f"{val} world"

    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_do(_action)

    result = subject("hello")

    assert result == "hello world"


async def test_when_then_do_async(decoy: Decoy) -> None:
    """It calls a function."""

    def _sync_action(val: str) -> str:
        return f"{val} world"

    async def _async_action(val: str) -> str:
        return f"{val} world"

    subject = decoy.mock(name="subject", is_async=True)
    decoy.when(subject).called_with("hello").then_do(_sync_action)
    decoy.when(subject).called_with("hola").then_do(_async_action)

    result = [
        await subject("hello"),
        await subject("hola"),
    ]

    assert result == ["hello world", "hola world"]


def test_when_then_do_invalid_async_action(decoy: Decoy) -> None:
    """It calls a function."""

    async def _action(val: str) -> str:
        return f"{val} world"

    subject = decoy.mock(name="subject")

    with pytest.raises(errors.MockNotAsyncError):
        decoy.when(subject).called_with("hello").then_do(_action)


def test_when_then_enter_with(decoy: Decoy) -> None:
    """It enters a context manager a function."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_enter_with("world")

    with subject("hello") as result:
        assert result == "world"


def test_when_then_return_while_entered(decoy: Decoy) -> None:
    """It enters a context manager a function."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("hola")
    decoy.when(subject, is_entered=True).called_with("hello").then_return("world")

    result = [subject("hello")]

    with subject:
        result.append(subject("hello"))

    assert result == ["hola", "world"]
