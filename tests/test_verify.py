"""Smoke and acceptance tests for main Decoy interface."""

from typing import Optional

import pytest

from decoy import Decoy, errors

from .fixtures import (
    SomeAsyncClass,
    SomeClass,
    SomeNestedClass,
    some_func,
)


def test_verify(decoy: Decoy) -> None:
    """It should be able to configure a verification with a rehearsal."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"))
    decoy.verify(subject(val="hello"))

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


def test_verify_call_list(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject_1 = decoy.mock(cls=SomeClass)
    subject_2 = decoy.mock(cls=SomeNestedClass)

    subject_1.foo("hello")
    subject_2.child.bar(1, 2.0, "3")
    subject_1.foo("goodbye")

    decoy.verify(
        subject_1.foo("hello"),
        subject_2.child.bar(1, 2.0, "3"),
        subject_1.foo("goodbye"),
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject_1.foo("hello"),
            subject_1.foo("goodbye"),
            subject_2.child.bar(1, 2.0, "3"),
        )


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


def test_verify_property_access(decoy: Decoy) -> None:
    """It should be able to verify property setters and deleters."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1.hello("world")
    subject_1.some_property = "fizzbuzz"
    del subject_2.another_property
    subject_2.answer(42)

    decoy.verify(
        subject_1.hello("world"),
        decoy.prop(subject_1.some_property).set("fizzbuzz"),
        decoy.prop(subject_2.another_property).delete(),
        subject_2.answer(42),
    )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject_1.hello("world"),
            decoy.prop(subject_1.some_property).set("fizzbuzz"),
            subject_2.answer(42),
            decoy.prop(subject_2.another_property).delete(),
        )
