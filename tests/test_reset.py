"""Tests for Decoy.reset."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import warnings as stdlib_warnings

import pytest

from decoy import warnings

if sys.version_info >= (3, 10):
    from decoy.next import Decoy

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="v3 preview only supports Python >= 3.10",
)


def test_reset_miscalled_stub_warning(decoy: Decoy) -> None:
    """It raises a MiscalledStubWarning at reset if calls don't match stubbings."""
    subject = decoy.mock(name="subject")

    decoy.when(subject).called_with("hello").then_return("hello world")
    subject("goodbye")

    with pytest.warns(warnings.MiscalledStubWarning) as warnings_log:
        decoy.reset()

    assert str(warnings_log[0].message) == os.linesep.join(
        [
            "Stub was called but no matching rehearsal found.",
            "Found 1 rehearsal:",
            "1.\tsubject('hello')",
            "Found 1 call:",
            "1.\tsubject('goodbye')",
        ]
    )


def test_reset_no_warning_without_stubs(decoy: Decoy) -> None:
    """It does not warn if the mock has no stubs configured."""
    subject = decoy.mock(name="subject")
    subject("anything")

    with stdlib_warnings.catch_warnings():
        stdlib_warnings.simplefilter("error", warnings.MiscalledStubWarning)
        decoy.reset()


def test_reset_no_warning_when_call_matches(decoy: Decoy) -> None:
    """It does not warn if every call matched a stub."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("world")
    subject("hello")

    with stdlib_warnings.catch_warnings():
        stdlib_warnings.simplefilter("error", warnings.MiscalledStubWarning)
        decoy.reset()


def test_reset_no_warning_when_verified(decoy: Decoy) -> None:
    """It does not warn if a non-matching call was later verified."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("world")
    subject("goodbye")
    decoy.verify(subject).called_with("goodbye")

    with stdlib_warnings.catch_warnings():
        stdlib_warnings.simplefilter("error", warnings.MiscalledStubWarning)
        decoy.reset()


def test_reset_warning_verify_ordering(decoy: Decoy) -> None:
    """It still warns for a call that occurs after a verify, not covered by it."""
    subject = decoy.mock(name="subject")
    decoy.when(subject).called_with("hello").then_return("world")

    subject("goodbye")
    decoy.verify(subject).called_with("goodbye")
    subject("goodbye")  # second call — not covered by the verify above

    with pytest.warns(warnings.MiscalledStubWarning):
        decoy.reset()


def test_reset_miscalled_stub_warning_call_site() -> None:
    """Warning call site points to the actual call, not reset."""
    script = textwrap.dedent("""
        from decoy.next import Decoy
        decoy = Decoy()
        subject = decoy.mock(name="subject")
        decoy.when(subject).called_with("hello").then_return("world")
        subject("goodbye")
        decoy.reset()
    """).strip()

    with stdlib_warnings.catch_warnings(record=True) as log:
        stdlib_warnings.simplefilter("always")
        exec(compile(script, filename="<test_callsite>", mode="exec"))  # noqa: S102

    assert log[0].filename == "<test_callsite>"
    assert log[0].lineno == 5  # subject("goodbye") is line 5 in the script
