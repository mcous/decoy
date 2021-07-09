"""Tests for error and warning message generation."""
import pytest
import os
from typing import List, NamedTuple

from decoy.spy import SpyCall, SpyRehearsal
from decoy.warnings import MiscalledStubWarning


class MiscalledStubSpec(NamedTuple):
    """Spec data for MiscalledStubWarning message tests."""

    rehearsals: List[SpyRehearsal]
    calls: List[SpyCall]
    expected_message: str


miscalled_stub_specs = [
    MiscalledStubSpec(
        rehearsals=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
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
    MiscalledStubSpec(
        rehearsals=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyRehearsal(spy_id=1, spy_name="spy", args=(0,), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
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
    MiscalledStubSpec(
        rehearsals=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(2,), kwargs={}),
        ],
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
]


@pytest.mark.parametrize(MiscalledStubSpec._fields, miscalled_stub_specs)
def test_verify_no_misscalled_stubs(
    rehearsals: List[SpyRehearsal],
    calls: List[SpyCall],
    expected_message: str,
) -> None:
    """It should stringify MiscalledStubWarning properly."""
    warning = MiscalledStubWarning(calls=calls, rehearsals=rehearsals)
    assert str(warning) == expected_message
