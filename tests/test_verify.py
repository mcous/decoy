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

    decoy.verify.called(subject)


def test_verify_args(decoy: Decoy) -> None:
    """It no-ops if a call is verified with args."""
    subject = decoy.mock(name="subject")

    subject("hello", world=True)

    decoy.verify.called(subject, "hello", world=True)


async def test_verify_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject()

    decoy.verify.called(subject)


async def test_verify_args_async(decoy: Decoy) -> None:
    """It no-ops if an async call is verified with args."""
    subject = decoy.mock(name="subject", is_async=True)

    await subject("hello", world=True)

    decoy.verify.called(subject, "hello", world=True)


def test_verify_missing_mock(decoy: Decoy) -> None:
    """It raises an exception if called without a mock."""
    with pytest.raises(errors.NotAMockError):
        decoy.verify.called(fixtures.noop)


def test_verify_fail(decoy: Decoy) -> None:
    """It fails verification if there were no calls."""
    subject = decoy.mock(name="subject")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify.called(subject)

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
        decoy.verify.called(subject)


def test_verify_fail_wrong_call(decoy: Decoy) -> None:
    """It fails verification if call was wrong."""
    subject = decoy.mock(name="subject")

    subject("hola", "mundo")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify.called(subject, "hello")

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
        decoy.verify.called(subject, "hello")

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
        decoy.verify.called(subject, **verify_kwargs)


def test_verify_times_pass(decoy: Decoy) -> None:
    """It can check call count."""
    subject = decoy.mock(name="subject")

    subject("hello")

    decoy.verify(times=1).called(subject, "hello")
    decoy.verify(times=0).called(subject, "goodbye")


def test_verify_times_fail(decoy: Decoy) -> None:
    """It fails if call count is wrong."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError) as exc_info:
        decoy.verify(times=0).called(subject, "hello")

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
        decoy.verify(times=1).called(subject, "hello")

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

    decoy.verify(ignore_extra_args=True).called(subject, "some-id")

    with pytest.raises(errors.VerifyError):
        decoy.verify(ignore_extra_args=True).called(subject, "wrong-id")

    with pytest.raises(errors.VerifyError):
        decoy.verify(ignore_extra_args=True).called(subject, "some-id", 999)

    with pytest.raises(errors.VerifyError):
        decoy.verify(ignore_extra_args=True).called(
            subject,
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

    decoy.verify(ignore_extra_args=True).called(subject, id="some-id")  # type: ignore[call-arg]

    with pytest.raises(errors.SignatureMismatchError):
        decoy.verify(ignore_extra_args=True).called(subject, not_id="wrong-id")  # type: ignore[call-arg]


async def test_verify_is_entered(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError):
        decoy.verify(is_entered=True).called(subject, "hello")

    with subject:
        subject("hello")

    decoy.verify(is_entered=True).called(subject, "hello")


async def test_verify_is_entered_ignore_extra_args(decoy: Decoy) -> None:
    """It verifies that a call happens while context manager entered."""
    subject = decoy.mock(name="subject")

    subject("hello")

    with pytest.raises(errors.VerifyError):
        decoy.verify(is_entered=True, ignore_extra_args=True).called(subject)

    with subject:
        subject("hello")

    decoy.verify(is_entered=True, ignore_extra_args=True).called(subject)


def test_verify_match_signature_in_called_with(decoy: Decoy) -> None:
    """It binds to signature in `called` when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject("hello", b=False)

    decoy.verify.called(subject, a="hello", b=False)


def test_verify_match_signature_in_call(decoy: Decoy) -> None:
    """It binds to signature in call when using args and kwargs."""
    subject = decoy.mock(func=fixtures.some_func_with_args_and_kwargs)

    subject(a="hello", b=False)

    decoy.verify.called(subject, "hello", b=False)


def test_verify_call_list_pass(decoy: Decoy) -> None:
    """It should be able to verify a call sequence."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2("world")

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "hello")
        verify.called(subject_2, "world")


def test_verify_call_list_pass_with_children(decoy: Decoy) -> None:
    """It should be able to verify a call sequence including child mocks."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("hello")
    subject_2.foo("world")

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "hello")
        verify.called(subject_2.foo, "world")


def test_verify_call_list_pass_ignore_before_and_after(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, ignoring calls before and after."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_1("before")
    subject_1("hello")
    subject_2("world")
    subject_2("after")

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "hello")
        verify.called(subject_2, "world")


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

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "a")
        verify.called(subject_2, "b")
        verify.called(subject_3, "c")


def test_verify_call_list_pass_other_mock(decoy: Decoy) -> None:
    """It should be able to verify a call sequence, even with a non-verified mock gettting called."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_3("c")

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "a")
        verify.called(subject_3, "c")


def test_verify_call_list_pass_multiple_calls(decoy: Decoy) -> None:
    """It should be able to verify a call sequence that includes the same call twice."""
    subject = decoy.mock(name="subject")

    subject("hello")
    subject("world")
    subject("hello")

    with decoy.verify.ordered as verify:
        verify.called(subject, "hello")
        verify.called(subject, "world")
        verify.called(subject, "hello")


def test_verify_call_list_fail_wrong_order(decoy: Decoy) -> None:
    """It fails a call sequence if there calls are in the wrong order."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")

    subject_2("world")
    subject_1("hello")

    with pytest.raises(errors.VerifyOrderError) as exc_info:
        with decoy.verify.ordered as verify:
            verify.called(subject_1, "hello")
            verify.called(subject_2, "world")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Call made out of order.",
            "",
            "Expected:",
            "\tsubject_2('world')",
            "to occur after:",
            "\tsubject_1('hello')",
            "",
            "Actual calls, in order:",
            "1.\tsubject_2('world')",
            "2.\tsubject_1('hello')",
        ]
    )


def test_verify_call_list_pass_interleaved_repeat(decoy: Decoy) -> None:
    """It allows a repeat of an already-matched call interleaved in the sequence."""
    subject_1 = decoy.mock(name="subject_1")
    subject_2 = decoy.mock(name="subject_2")
    subject_3 = decoy.mock(name="subject_3")

    subject_1("a")
    subject_2("b")
    subject_1("a")
    subject_3("c")

    with decoy.verify.ordered as verify:
        verify.called(subject_1, "a")
        verify.called(subject_2, "b")
        verify.called(subject_3, "c")


def test_verify_call_list_times_pass(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject = decoy.mock(name="subject")

    subject("before")
    subject("hello")
    subject("hello")
    subject("after")

    with decoy.verify.ordered as verify:
        verify(times=2).called(subject, "hello")
        verify(times=1).called(subject, "after")


def test_verify_call_list_times_fail(decoy: Decoy) -> None:
    """It should be able to verify multiple calls."""
    subject = decoy.mock(name="subject")

    subject("hello")
    subject("hello")
    subject("world")
    subject("world")
    subject("hello")

    with pytest.raises(errors.VerifyOrderError) as exc_info:
        with decoy.verify.ordered as verify:
            verify(times=3).called(subject, "hello")
            verify.called(subject, "world")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Call made out of order.",
            "",
            "Expected:",
            "\tsubject('world')",
            "to occur after:",
            "\tsubject('hello')",
            "",
            "Actual calls, in order:",
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
        with decoy.verify as verify:
            verify.set(subject.some_property).to("42")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.some_property = '42'",
            "Found 0 calls.",
        ]
    )


def test_verify_attribute_set_incorrect(decoy: Decoy) -> None:
    """It fails if attribute was set to the wrong value."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    with pytest.raises(errors.VerifyError) as exc_info:
        with decoy.verify as verify:
            verify.set(subject.some_property).to("43")

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tsubject.some_property = '43'",
            "Found 1 call:",
            "1.\tsubject.some_property = '42'",
        ]
    )


def test_verify_attribute_set(decoy: Decoy) -> None:
    """It passes if attribute was set."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"

    with decoy.verify as verify:
        verify.set(subject.some_property).to("42")


def test_verify_attribute_set_missing_rehearsal(decoy: Decoy) -> None:
    """It does not mistake attribute access for a mock rehearsal."""
    _ = decoy.mock(name="subject").foo

    with pytest.raises(errors.NotAMockError):
        decoy.verify.called(fixtures.noop)


def test_verify_attribute_multiple_sets(decoy: Decoy) -> None:
    """It can verify an earlier attribute set."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    subject.some_property = "43"

    with decoy.verify as verify:
        verify.set(subject.some_property).to("42")


def test_verify_attribute_set_then_delete(decoy: Decoy) -> None:
    """It can verify an attribute set even after it is deleted."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    del subject.some_property

    with decoy.verify as verify:
        verify.set(subject.some_property).to("42")


def test_verify_attribute_delete(decoy: Decoy) -> None:
    """It verifies an attribute delete."""
    subject = decoy.mock(name="subject")

    del subject.some_property

    with decoy.verify as verify:
        verify.delete(subject.some_property)

    with pytest.raises(errors.VerifyError) as exc_info:
        with decoy.verify as verify:
            verify.delete(subject.other_property)

    assert str(exc_info.value) == os.linesep.join(
        [
            "Expected at least 1 call:",
            "1.\tdel subject.other_property",
            "Found 0 calls.",
        ]
    )


def test_verify_attribute_nested_blocks(decoy: Decoy) -> None:
    """It restores the outer block's paused state when a nested block exits."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    subject.other_property = "43"

    with decoy.verify as outer:
        with decoy.verify as inner:
            inner.set(subject.some_property).to("42")

        outer.set(subject.other_property).to("43")


def test_verify_attribute_set_times(decoy: Decoy) -> None:
    """It threads per-check options into attribute verification within a block."""
    subject = decoy.mock(name="subject")

    subject.some_property = "42"
    subject.some_property = "42"

    with decoy.verify as verify:
        verify(times=2).set(subject.some_property).to("42")

    with pytest.raises(errors.VerifyError):
        with decoy.verify as verify:
            verify(times=1).set(subject.some_property).to("42")


def test_redundant_verify(decoy: Decoy) -> None:
    """It raises a RedundantVerifyWarning if verify call matches stubbing."""
    subject = decoy.mock(name="subject")

    decoy.when.called(subject, "goodbye").then_return("adios")
    decoy.when.called(subject, "hello").then_return("hello world")

    subject("hello")

    with pytest.warns(warnings.RedundantVerifyWarning) as warnings_log:
        decoy.verify.called(subject, "hello")

    assert str(warnings_log[0].message) == os.linesep.join(
        [
            "The same `called` arguments were used with both `when` and `verify`.",
            "This is redundant and probably a misuse of the mock.",
            "\tsubject('hello')",
            "See https://michael.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",
        ]
    )
