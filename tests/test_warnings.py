"""Tests for error and warning message generation."""
import pytest
import os
from typing import NamedTuple

from decoy.spy_events import SpyCall, SpyEvent, SpyInfo, WhenRehearsal, VerifyRehearsal
from decoy.warnings import DecoyWarning, MiscalledStubWarning, RedundantVerifyWarning


class WarningSpec(NamedTuple):
    """Spec data for MiscalledStubWarning message tests."""

    warning: DecoyWarning
    expected_message: str


warning_specs = [
    WarningSpec(
        warning=MiscalledStubWarning(
            rehearsals=[
                WhenRehearsal(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(), kwargs={})
                ),
            ],
            calls=[
                SpyEvent(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(1,), kwargs={})
                ),
            ],
        ),
        expected_message=os.linesep.join(
            [
                "Stub was called but no matching rehearsal found.",
                "Found 1 rehearsal:",
                "1.\tspy()",
                "Found 1 call:",
                "1.\tspy(1)",
            ]
        ),
    ),
    WarningSpec(
        warning=MiscalledStubWarning(
            rehearsals=[
                WhenRehearsal(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(), kwargs={})
                ),
                WhenRehearsal(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(0,), kwargs={})
                ),
            ],
            calls=[
                SpyEvent(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(1,), kwargs={})
                ),
            ],
        ),
        expected_message=os.linesep.join(
            [
                "Stub was called but no matching rehearsal found.",
                "Found 2 rehearsals:",
                "1.\tspy()",
                "2.\tspy(0)",
                "Found 1 call:",
                "1.\tspy(1)",
            ]
        ),
    ),
    WarningSpec(
        warning=MiscalledStubWarning(
            rehearsals=[
                WhenRehearsal(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(), kwargs={})
                ),
            ],
            calls=[
                SpyEvent(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(1,), kwargs={})
                ),
                SpyEvent(
                    spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(2,), kwargs={})
                ),
            ],
        ),
        expected_message=os.linesep.join(
            [
                "Stub was called but no matching rehearsal found.",
                "Found 1 rehearsal:",
                "1.\tspy()",
                "Found 2 calls:",
                "1.\tspy(1)",
                "2.\tspy(2)",
            ]
        ),
    ),
    WarningSpec(
        warning=RedundantVerifyWarning(
            rehearsal=VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy"), payload=SpyCall(args=(1,), kwargs={})
            ),
        ),
        expected_message=os.linesep.join(
            [
                "The same rehearsal was used in both a `when` and a `verify`.",
                "This is redundant and probably a misuse of the mock.",
                "\tspy(1)",
                "See https://mike.cousins.io/decoy/usage/errors-and-warnings/#redundantverifywarning",  # noqa: E501
            ]
        ),
    ),
]


@pytest.mark.parametrize(WarningSpec._fields, warning_specs)
def test_warning(warning: DecoyWarning, expected_message: str) -> None:
    """It should stringify warnings properly."""
    assert str(warning) == expected_message
