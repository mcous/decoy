"""Smoke and acceptance tests for main Decoy interface."""

import os
from typing import Dict, Optional

import pytest

from decoy import Decoy, errors
from decoy.warnings import RedundantVerifyWarning

from . import fixtures


def test_verify(decoy: Decoy) -> None:
    """It no-ops if a call is verified."""
    subject = decoy.mock(name="subject")

    subject()

    decoy.verify(subject())


def test_verify_args(decoy: Decoy) -> None:
    """It no-ops if a call is verified with args."""
    subject = decoy.mock(name="subject")

    subject("hello", world=True)

    decoy.verify(subject("hello", world=True))


async def test_verify_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject()

    decoy.verify(await subject())


async def test_verify_args_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified with args."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject("hello", world=True)

    decoy.verify(await subject("hello", world=True))


def test_verify_missing_rehearsal(decoy: Decoy) -> None:
    """It raises an exception if called without a mock."""
    with pytest.raises(errors.MissingRehearsalError):
        decoy.verify(fixtures.noop())


def test_verify_missing_rehearsal_after_success(decoy: Decoy) -> None:
    """It raises an exception if called without a mock even after a successful rehearsal."""
    subject = decoy.mock(name="subject")

    subject()

    decoy.verify(subject())

    with pytest.raises(errors.MissingRehearsalError):
        decoy.verify(fixtures.noop())


def test_verify_fail(decoy: Decoy) -> None:
    """It fails verification if there were no calls."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject())

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject()",
            "Found 0 calls.",
        ]
    )


def test_verify_reset(decoy: Decoy) -> None:
    """It resets the call log."""
    subject = decoy.mock(name="subject")

    subject()
    decoy.reset()

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject())


def test_verify_fail_wrong_call(decoy: Decoy) -> None:
    """It fails verification if call was wrong."""
    subject = decoy.mock(name="subject")

    subject("hola", "mundo")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject('hello')",
            "Found 1 call:",
            "1.\tsubject('hola', 'mundo')",
        ]
    )

    subject("adios")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject('hello')",
            "Found 2 calls:",
            "1.\tsubject('hola', 'mundo')",
            "2.\tsubject('adios')",
        ]
    )


@pytest.mark.parametrize(
    ("verify_kwargs"),
    [
        {"greeting": "hello", "count": 1, "opts": {"world": False}},
        {"greeting": "hello", "count": 2, "opts": {"world": True}},
        {"greeting": "goodbye", "count": 1, "opts": {"world": True}},
        {"greeting": "hello", "count": 1},
    ],
)
def test_verify_kwargs_fail(decoy: Decoy, verify_kwargs: Dict[str, object]) -> None:
    """It verifies kwargs for a call do not match."""
    subject = decoy.mock(name="subject")

    subject(greeting="hello", count=1, opts={"world": True})

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject(**verify_kwargs))


def test_verify_times_pass(decoy: Decoy) -> None:
    """It can check call count."""
    subject = decoy.mock(name="subject")

    subject("hello")

    decoy.verify(subject("hello"), times=1)
    decoy.verify(subject("goodbye"), times=0)


def test_verify_times_fail(decoy: Decoy) -> None:
    """It fails if call count is wrong."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"), times=0)

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 0 calls:",
            "1.\tsubject('hello')",
            "Found 1 call.",
        ]
    )

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject("hello"), times=1)

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 1 call:",
            "1.\tsubject('hello')",
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


def test_verify_match_signature_in_called_with(decoy: Decoy) -> None:
    """It binds to signature in `called_with` when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject("hello", b=False)

    decoy.verify(subject(a="hello", b=False))


def test_verify_match_signature_in_call(decoy: Decoy) -> None:
    """It binds to signature in call when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject(a="hello", b=False)

    decoy.verify(subject("hello", b=False))


def test_verify_call_list_pass(decoy: Decoy) -> None:
    """It should be able to verify a call sequence."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2("world")

    decoy.verify(subject_1("hello"), subject_2("world"))


def test_verify_call_list_pass_with_children(decoy: Decoy) -> None:
    """It should be able to verify a call sequence including child mocks."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2.foo("world")

    decoy.verify(subject_1("hello"), subject_2.foo("world"))


def test_verify_call_list_pass_ignore_before_and_after(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, ignoring calls before and after."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("before")
    subject_1("hello")
    subject_2("world")
    subject_2("after")

    decoy.verify(subject_1("hello"), subject_2("world"))


def test_verify_call_list_pass_false_start(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, even with a false start."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_1("a")
    subject_2("b")
    subject_3("c")

    decoy.verify(subject_1("a"), subject_2("b"), subject_3("c"))


def test_verify_call_list_pass_other_mock(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, even with a non-verified mock gettting called."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_3("c")

    decoy.verify(subject_1("a"), subject_3("c"))


def test_verify_call_list_fail_no_calls(decoy: Decoy) -> None:
    """It fails a call sequence if there are no calls."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject_1("hello"), subject_2("world"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tsubject_1('hello')",
            "2.\tsubject_2('world')",
            "Found 0 calls.",
        ]
    )


def test_verify_call_list_fail_wrong_order(decoy: Decoy) -> None:
    """It fails a call sequence if there calls are in the wrong order."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_2("world")
    subject_1("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject_1("hello"), subject_2("world"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tsubject_1('hello')",
            "2.\tsubject_2('world')",
            "Found 2 calls:",
            "1.\tsubject_2('world')",
            "2.\tsubject_1('hello')",
        ]
    )


def test_verify_call_list_fail_extra_call(decoy: Decoy) -> None:
    """It fails a call sequence if there is an extra call in the wrong place."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_1("a")
    subject_3("c")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject_1("a"), subject_2("b"), subject_3("c"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tsubject_1('a')",
            "2.\tsubject_2('b')",
            "3.\tsubject_3('c')",
            "Found 4 calls:",
            "1.\tsubject_1('a')",
            "2.\tsubject_2('b')",
            "3.\tsubject_1('a')",
            "4.\tsubject_3('c')",
        ]
    )


def test_verify_attribute_set(decoy: Decoy) -> None:
    """It verifies an attribute set."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    decoy.verify(decoy.prop(subject.some_property).set("42"))

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(decoy.prop(subject.some_property).set("43"))

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.some_property = 43",
            "Found 1 call:",
            "1.\tsubject.some_property = 42",
        ]
    )


def test_verify_attribute_delete(decoy: Decoy) -> None:
    """It verifies an attribute delete."""
    subject = decoy.mock(name="subject")

    del subject.some_property

    decoy.verify(decoy.prop(subject.some_property).delete())

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(decoy.prop(subject.other_property).delete())

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tdel subject.other_property",
            "Found 1 call:",
            "1.\tdel subject.some_property",
        ]
    )


def test_redundant_verify(decoy: Decoy) -> None:
    """It raises a RedundantVerifyWarning if verify call matches stubbing."""
    subject = decoy.mock(name="subject")

    decoy.when(subject("hello")).then_return("hello world")

    subject("hello")

    decoy.verify(subject("hello"))

    with pytest.warns(RedundantVerifyWarning) as warnings:
        decoy.reset()

    assert str(warnings[0].message) == os.linesep.join(
        [
            "The same rehearsal was used in both a `when` and a `verify`.",
            "This is redundant and probably a misuse of the mock.",
            "\tsubject('hello')",
            "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
        ]
    )
