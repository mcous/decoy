"""Test for Decoy.verify."""

from typing import Any, Dict, Tuple

import pytest

from decoy.next import Decoy
from decoy.next.errors import NotAMockError, VerifyError

from ..fixtures import some_func


def test_verify_not_mock(decoy: Decoy) -> None:
    """It raises an exception if passed not a mock."""
    with pytest.raises(NotAMockError):
        decoy.verify(some_func)


def test_verify_no_calls(decoy: Decoy) -> None:
    """It raises an exception if the mock has no calls."""
    subject = decoy.mock(name="subject")

    with pytest.raises(VerifyError):
        decoy.verify(subject).called_with("hello")


def test_verify_no_args(decoy: Decoy) -> None:
    """It verifies a single call."""
    subject = decoy.mock(name="subject")

    subject()

    decoy.verify(subject).called_with()


def test_verify_reset(decoy: Decoy) -> None:
    """It resets the call log."""
    subject = decoy.mock(name="subject")

    subject()
    decoy.reset()

    with pytest.raises(VerifyError):
        decoy.verify(subject).called_with()


async def test_verify_async_no_args(decoy: Decoy) -> None:
    """It verifies a single async call."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject()

    decoy.verify(subject).called_with()


def test_verify_args_pass(decoy: Decoy) -> None:
    """It verifies args match."""
    subject = decoy.mock(name="subject")

    subject("hello", 1, {"world": True})

    decoy.verify(subject).called_with("hello", 1, {"world": True})


@pytest.mark.parametrize(
    ("verify_args"),
    [
        ("hello", 1, {"world": False}),
        ("hello", 2, {"world": True}),
        ("goodbye", 1, {"world": True}),
        ("hello", 1),
    ],
)
def test_verify_args_fail(decoy: Decoy, verify_args: Tuple[Any, ...]) -> None:
    """It verifies args do not match."""
    subject = decoy.mock(name="subject")

    subject("hello", 1, {"world": True})

    with pytest.raises(VerifyError):
        decoy.verify(subject).called_with(*verify_args)


def test_verify_kwargs_pass(decoy: Decoy) -> None:
    """It can verifies that kwargs for a call match."""
    subject = decoy.mock(name="subject")

    subject(greeting="hello", count=1, opts={"world": True})

    decoy.verify(subject).called_with(greeting="hello", count=1, opts={"world": True})


@pytest.mark.parametrize(
    ("verify_kwargs"),
    [
        {"greeting": "hello", "count": 1, "opts": {"world": False}},
        {"greeting": "hello", "count": 2, "opts": {"world": True}},
        {"greeting": "goodbye", "count": 1, "opts": {"world": True}},
        {"greeting": "hello", "count": 1},
    ],
)
def test_verify_kwargs_fail(decoy: Decoy, verify_kwargs: Dict[str, Any]) -> None:
    """It verifies kwargs for a call do not match."""
    subject = decoy.mock(name="subject")

    subject(greeting="hello", count=1, opts={"world": True})

    with pytest.raises(VerifyError):
        decoy.verify(subject).called_with(**verify_kwargs)


async def test_verify_times(decoy: Decoy) -> None:
    """It verifies call count."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(VerifyError):
        decoy.verify(subject, times=2).called_with("hello")

    subject("hello")

    decoy.verify(subject, times=2).called_with("hello")


async def test_verify_ignore_extra_args(decoy: Decoy) -> None:
    """It verifies while ignoring extra args."""
    subject = decoy.mock(name="subject")

    subject("hello", "world")

    decoy.verify(subject, ignore_extra_args=True).called_with("hello")


async def test_verify_ignore_extra_kwargs(decoy: Decoy) -> None:
    """It verifies while ignoring extra kwargs."""
    subject = decoy.mock(name="subject")

    subject("abc", greeting="hello", count=1)

    decoy.verify(subject, ignore_extra_args=True).called_with(greeting="hello")
    decoy.verify(subject, ignore_extra_args=True).called_with(count=1)


async def test_verify_is_entered(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(VerifyError):
        decoy.verify(subject, is_entered=True).called_with("hello")

    with subject:
        subject("hello")

    decoy.verify(subject, is_entered=True).called_with("hello")


async def test_verify_is_entered_ignore_extra_args(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(VerifyError):
        decoy.verify(subject, is_entered=True, ignore_extra_args=True).called_with()

    with subject:
        subject("hello")

    decoy.verify(subject, is_entered=True).called_with("hello")
