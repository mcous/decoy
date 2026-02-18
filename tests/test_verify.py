"""Smoke and acceptance tests for main Decoy interface."""

from __future__ import annotations

import os
import sys

import pytest

from decoy import errors, warnings

from . import fixtures

if sys.version_info >= (3, 10):
    from decoy.next import Decoy


pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


def test_verify(decoy: Decoy) -> None:
    """It no-ops if a call is verified."""
    subject = decoy.mock(name="subject")

    subject()

    decoy.verify(subject).called_with()


def test_verify_args(decoy: Decoy) -> None:
    """It no-ops if a call is verified with args."""
    subject = decoy.mock(name="subject")

    subject("hello", world=True)

    decoy.verify(subject).called_with("hello", world=True)


async def test_verify_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject()

    decoy.verify(subject).called_with()


async def test_verify_args_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified with args."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject("hello", world=True)

    decoy.verify(subject).called_with("hello", world=True)


def test_verify_missing_mock(decoy: Decoy) -> None:
    """It raises an exception if called without a mock."""
    with pytest.raises(errors.NotAMockError):
        decoy.verify(fixtures.noop)


def test_verify_fail(decoy: Decoy) -> None:
    """It fails verification if there were no calls."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject).called_with()

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
        decoy.verify(subject).called_with()


def test_verify_fail_wrong_call(decoy: Decoy) -> None:
    """It fails verification if call was wrong."""
    subject = decoy.mock(name="subject")

    subject("hola", "mundo")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject).called_with("hello")

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
        decoy.verify(subject).called_with("hello")

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
def test_verify_kwargs_fail(decoy: Decoy, verify_kwargs: dict[str, object]) -> None:
    """It verifies kwargs for a call do not match."""
    subject = decoy.mock(name="subject")

    subject(greeting="hello", count=1, opts={"world": True})

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject).called_with(**verify_kwargs)


def test_verify_times_pass(decoy: Decoy) -> None:
    """It can check call count."""
    subject = decoy.mock(name="subject")

    subject("hello")

    decoy.verify(subject, times=1).called_with("hello")
    decoy.verify(subject, times=0).called_with("goodbye")


def test_verify_times_fail(decoy: Decoy) -> None:
    """It fails if call count is wrong."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject, times=0).called_with("hello")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 0 calls:",
            "1.\tsubject('hello')",
            "Found 1 call:",
            "1.\tsubject('hello')",
        ]
    )

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject, times=1).called_with("hello")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected exactly 1 call:",
            "1.\tsubject('hello')",
            "Found 2 calls:",
            "1.\tsubject('hello')",
            "2.\tsubject('hello')",
        ]
    )


def test_verify_ignore_extra_args(decoy: Decoy) -> None:
    """It should be able to ignore extra args in a stub rehearsal."""

    def _get_a_thing(id: str, default: int | None = None, message: str = "") -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    subject("some-id", 101)

    decoy.verify(subject, ignore_extra_args=True).called_with("some-id")

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject, ignore_extra_args=True).called_with("wrong-id")

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject, ignore_extra_args=True).called_with("some-id", 999)

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject, ignore_extra_args=True).called_with(
            "some-id",
            101,
            "oops",
        )


def test_verify_ignore_extra_args_signature(decoy: Decoy) -> None:
    """It does not raise a signature mismatch error when ignore_extra_args is set."""

    def _get_a_thing(id: str, default: int, message: str) -> int:
        raise NotImplementedError("intentionally unimplemented")

    subject = decoy.mock(func=_get_a_thing)

    subject("some-id", 101, "hello")

    decoy.verify(subject, ignore_extra_args=True).called_with(id="some-id")  # type: ignore[call-arg]

    with pytest.raises(errors.SignatureMismatchError):
        decoy.verify(subject, ignore_extra_args=True).called_with(not_id="wrong-id")  # type: ignore[call-arg]


async def test_verify_is_entered(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject, is_entered=True).called_with("hello")

    with subject:
        subject("hello")

    decoy.verify(subject, is_entered=True).called_with("hello")


async def test_verify_is_entered_ignore_extra_args(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError):
        decoy.verify(subject, is_entered=True, ignore_extra_args=True).called_with()

    with subject:
        subject("hello")

    decoy.verify(subject, is_entered=True, ignore_extra_args=True).called_with()


def test_verify_match_signature_in_called_with(decoy: Decoy) -> None:
    """It binds to signature in `called_with` when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject("hello", b=False)

    decoy.verify(subject).called_with(a="hello", b=False)


def test_verify_match_signature_in_call(decoy: Decoy) -> None:
    """It binds to signature in call when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject(a="hello", b=False)

    decoy.verify(subject).called_with("hello", b=False)


def test_verify_call_list_pass(decoy: Decoy) -> None:
    """It should be able to verify a call sequence."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2("world")

    with decoy.verify_order():
        decoy.verify(subject_1).called_with("hello")
        decoy.verify(subject_2).called_with("world")


def test_verify_call_list_pass_with_children(decoy: Decoy) -> None:
    """It should be able to verify a call sequence including child mocks."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2.foo("world")

    with decoy.verify_order():
        decoy.verify(subject_1).called_with("hello")
        decoy.verify(subject_2.foo).called_with("world")


def test_verify_call_list_pass_ignore_before_and_after(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, ignoring calls before and after."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("before")
    subject_1("hello")
    subject_2("world")
    subject_2("after")

    with decoy.verify_order():
        decoy.verify(subject_1).called_with("hello")
        decoy.verify(subject_2).called_with("world")


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

    with decoy.verify_order():
        decoy.verify(subject_1).called_with("a")
        decoy.verify(subject_2).called_with("b")
        decoy.verify(subject_3).called_with("c")


def test_verify_call_list_pass_other_mock(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, even with a non-verified mock gettting called."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_3("c")

    with decoy.verify_order():
        decoy.verify(subject_1).called_with("a")
        decoy.verify(subject_3).called_with("c")


def test_verify_call_list_pass_multiple_calls(decoy: Decoy) -> None:
    """It should be able to verify a call sequence that includes the same call twice."""
    subject = decoy.mock(name="subject")

    subject("hello")
    subject("world")
    subject("hello")

    with decoy.verify_order():
        decoy.verify(subject).called_with("hello")
        decoy.verify(subject).called_with("world")
        decoy.verify(subject).called_with("hello")


def test_verify_call_list_fail_wrong_order(decoy: Decoy) -> None:
    """It fails a call sequence if there calls are in the wrong order."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_2("world")
    subject_1("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        with decoy.verify_order():
            decoy.verify(subject_1).called_with("hello")
            decoy.verify(subject_2).called_with("world")

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
        with decoy.verify_order():
            decoy.verify(subject_1).called_with("a")
            decoy.verify(subject_2).called_with("b")
            decoy.verify(subject_3).called_with("c")

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


def test_verify_call_list_times_pass(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject = decoy.mock(name="subject")

    subject("before")
    subject("hello")
    subject("hello")
    subject("after")

    with decoy.verify_order():
        decoy.verify(subject, times=2).called_with("hello")
        decoy.verify(subject, times=1).called_with("after")


def test_verify_call_list_times_fail(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject = decoy.mock(name="subject")

    subject("hello")
    subject("hello")
    subject("world")
    subject("world")
    subject("hello")

    with pytest.raises(errors.VerifyOrderError) as exc_info:
        with decoy.verify_order():
            decoy.verify(subject, times=3).called_with("hello")
            decoy.verify(subject).called_with("world")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected call sequence:",
            "1.\tsubject('hello')",
            "2.\tsubject('hello')",
            "3.\tsubject('hello')",
            "4.\tsubject('world')",
            "Found 5 calls:",
            "1.\tsubject('hello')",
            "2.\tsubject('hello')",
            "3.\tsubject('world')",
            "4.\tsubject('world')",
            "5.\tsubject('hello')",
        ]
    )


def test_verify_attribute_set_missing(decoy: Decoy) -> None:
    """It fails if attribute was not set."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject.some_property).set("42")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.some_property = 42",
            "Found 0 calls.",
        ]
    )


def test_verify_attribute_set_incorrect(decoy: Decoy) -> None:
    """It fails if attribute was set to the wrong value."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject.some_property).set("43")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.some_property = 43",
            "Found 1 call:",
            "1.\tsubject.some_property = 42",
        ]
    )


def test_verify_attribute_set(decoy: Decoy) -> None:
    """It passes if attribute was set."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    decoy.verify(subject.some_property).set("42")


def test_verify_attribute_set_missing_rehearsal(decoy: Decoy) -> None:
    """It does not mistake attribute access for a mock rehearsal."""
    _ = decoy.mock(name="subject").foo

    with pytest.raises(errors.NotAMockError):
        decoy.verify(fixtures.noop)


def test_verify_attribute_multiple_sets(decoy: Decoy) -> None:
    """It can verify an earlier attribute set."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    subject.some_property = "43"

    decoy.verify(subject.some_property).set("42")


def test_verify_attribute_set_then_delete(decoy: Decoy) -> None:
    """It can verify an attribute set even after it is deleted."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    del subject.some_property

    decoy.verify(subject.some_property).set("42")


def test_verify_attribute_delete(decoy: Decoy) -> None:
    """It verifies an attribute delete."""
    subject = decoy.mock(name="subject")

    del subject.some_property

    decoy.verify(subject.some_property).delete()

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(subject.other_property).delete()

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tdel subject.other_property",
            "Found 0 calls.",
        ]
    )


def test_redundant_verify(decoy: Decoy) -> None:
    """It raises a RedundantVerifyWarning if verify call matches stubbing."""
    subject = decoy.mock(name="subject")

    decoy.when(subject).called_with("goodbye").then_return("adios")
    decoy.when(subject).called_with("hello").then_return("hello world")

    subject("hello")

    with pytest.warns(warnings.RedundantVerifyWarning) as warnings_log:
        decoy.verify(subject).called_with("hello")

    assert str(warnings_log[0].message) == os.linesep.join(
        [
            "The same rehearsal was used in both a `when` and a `verify`.",
            "This is redundant and probably a misuse of the mock.",
            "\tsubject('hello')",
            "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
        ]
    )
