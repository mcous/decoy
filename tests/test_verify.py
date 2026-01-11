"""Smoke and acceptance tests for main Decoy interface."""

import os
from typing import Optional

import pytest

from decoy import Decoy, errors
from decoy.warnings import RedundantVerifyWarning

from .fixtures import (
    SomeAsyncClass,
    SomeClass,
    SomeNestedClass,
    noop,
    some_func,
)


def test_verify_pass(decoy: Decoy) -> None:
    """It verifies a call by args and kwargs."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"))
    decoy.verify(subject(val="hello"))


def test_verify_missing_rehearsal(decoy: Decoy) -> None:
    """It raises MissingRehearsalError."""
    with pytest.raises(errors.MissingRehearsalError):
        decoy.verify(noop())


def test_verify_missing_rehearsal_after_success(decoy: Decoy) -> None:
    """It raises MissingRehearsalError after a successful rehearsal."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"))

    with pytest.raises(errors.MissingRehearsalError):
        decoy.verify(noop())


def test_verify_fail_no_calls(decoy: Decoy) -> None:
    """It fails verification if there were no calls."""
    subject = decoy.mock(func=some_func)

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsome_func('hello')",
            "Found 0 calls.",
        ]
    )


def test_verify_fail_wrong_call(decoy: Decoy) -> None:
    """It fails verification if there were no calls."""
    subject = decoy.mock(func=some_func)

    subject("hola")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsome_func('hello')",
            "Found 1 call:",
            "1.\tsome_func('hola')",
        ]
    )

    subject("goodbye")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsome_func('hello')",
            "Found 2 calls:",
            "1.\tsome_func('hola')",
            "2.\tsome_func('goodbye')",
        ]
    )


def test_verify_times_pass(decoy: Decoy) -> None:
    """It should be able to verify a call count."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    decoy.verify(subject("hello"), times=1)
    decoy.verify(subject("goodbye"), times=0)


def test_verify_times_fail_wrong_count(decoy: Decoy) -> None:
    """It should be able to verify a call count."""
    subject = decoy.mock(func=some_func)

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"), times=0)

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 0 calls:",
            "1.\tsome_func('hello')",
            "Found 1 call.",
        ]
    )

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"), times=1)

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 1 call:",
            "1.\tsome_func('hello')",
            "Found 2 calls.",
        ]
    )


def test_verify_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: Optional[int] = None, message: str = "") -> int:
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

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject("some-id", 999),
            ignore_extra_args=True,
        )

    with pytest.raises(errors.VerifyError):
        decoy.verify(
            subject("some-id", 101, "oops"),
            ignore_extra_args=True,
        )


def test_verify_call_list_pass(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject_1 = decoy.mock(cls=SomeClass)
    subject_2 = decoy.mock(cls=SomeNestedClass)

    subject_1.foo("before")
    subject_1.foo("hello")
    subject_2.child.bar(1, 2.0, "3")
    subject_1.foo("goodbye")
    subject_1.foo("after")

    decoy.verify(
        subject_1.foo("hello"),
        subject_2.child.bar(1, 2.0, "3"),
        subject_1.foo("goodbye"),
    )


def test_verify_call_list_fail(decoy: Decoy) -> None:
    """It fails multiple calls."""
    subject_1 = decoy.mock(cls=SomeClass)
    subject_2 = decoy.mock(cls=SomeNestedClass)

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(
            subject_1.foo("hello"),
            subject_2.child.bar(1, 2.0, "3"),
            subject_1.foo("goodbye"),
        )

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tSomeClass.foo('hello')",
            "2.\tSomeNestedClass.child.bar(1, 2.0, '3')",
            "3.\tSomeClass.foo('goodbye')",
            "Found 0 calls.",
        ]
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


def test_verify_property_set(decoy: Decoy) -> None:
    """It should be able to verify property setters and deleters."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    decoy.verify(decoy.prop(subject.some_property).set("42"))

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(decoy.prop(subject.other_property).set("42"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.other_property = 42",
            "Found 1 call:",
            "1.	subject.some_property = 42",
        ]
    )


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

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(
            subject_1.hello("world"),
            decoy.prop(subject_1.some_property).set("fizzbuzz"),
            subject_2.answer(42),
            decoy.prop(subject_2.another_property).delete(),
        )

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tsubject_1.hello('world')",
            "2.\tsubject_1.some_property = fizzbuzz",
            "3.\tsubject_2.answer(42)",
            "4.\tdel subject_2.another_property",
            "Found 4 calls:",
            "1.\tsubject_1.hello('world')",
            "2.\tsubject_1.some_property = fizzbuzz",
            "3.\tdel subject_2.another_property",
            "4.\tsubject_2.answer(42)",
        ]
    )


def test_redundant_verify(decoy: Decoy) -> None:
    """It raises a RedundantVerifyWarning if verify call matches stubbing."""
    subject = decoy.mock(func=some_func)

    decoy.when(subject("hello")).then_return("hello world")

    subject("hello")

    decoy.verify(subject("hello"))

    with pytest.warns(RedundantVerifyWarning) as warnings:
        decoy.reset()

    assert str(warnings[0].message) == os.linesep.join(
        [
            "The same rehearsal was used in both a `when` and a `verify`.",
            "This is redundant and probably a misuse of the mock.",
            "\tsome_func('hello')",
            "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
        ]
    )
