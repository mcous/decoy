"""Tests for error and warning message generation."""
import pytest
import os
from typing import List, NamedTuple, Optional

from decoy.errors import VerifyError
from decoy.call_stack import SpyCall, SpyRehearsal


class VerifyErrorSpec(NamedTuple):
    """Spec data for VerifyError tests."""

    rehearsals: List[SpyRehearsal]
    calls: List[SpyCall]
    times: Optional[int]
    expected_message: str


verify_error_specs = [
    VerifyErrorSpec(
        rehearsals=[
            SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        ],
        calls=[],
        times=None,
        expected_message=os.linesep.join(
            [
                "Expected at least 1 call:",
                "1.\tmy_spy()",
                "Found 0 calls.",
            ]
        ),
    ),
    VerifyErrorSpec(
        rehearsals=[
            SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
        ],
        times=None,
        expected_message=os.linesep.join(
            [
                "Expected at least 1 call:",
                "1.\tmy_spy()",
                "Found 2 calls:",
                "1.\tspy_101(1, 2, 3)",
                "2.\tspy_101(4, 5, 6)",
            ]
        ),
    ),
    VerifyErrorSpec(
        rehearsals=[
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
            SpyRehearsal(spy_id=202, spy_name="spy_202", args=(7, 8, 9), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
            SpyCall(spy_id=202, spy_name="spy_202", args=("oh no",), kwargs={}),
        ],
        times=None,
        expected_message=os.linesep.join(
            [
                "Expected call sequence:",
                "1.\tspy_101(1, 2, 3)",
                "2.\tspy_101(4, 5, 6)",
                "3.\tspy_202(7, 8, 9)",
                "Found 3 calls:",
                "1.\tspy_101(1, 2, 3)",
                "2.\tspy_101(4, 5, 6)",
                "3.\tspy_202('oh no')",
            ]
        ),
    ),
    VerifyErrorSpec(
        rehearsals=[
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        times=1,
        expected_message=os.linesep.join(
            [
                "Expected exactly 1 call:",
                "1.\tspy_101(1, 2, 3)",
                "Found 2 calls.",
            ]
        ),
    ),
]


@pytest.mark.parametrize(VerifyErrorSpec._fields, verify_error_specs)
def test_verify_error(
    rehearsals: List[SpyRehearsal],
    calls: List[SpyCall],
    times: Optional[int],
    expected_message: str,
) -> None:
    """It should stringify VerifyError properly."""
    error = VerifyError(rehearsals=rehearsals, calls=calls, times=times)
    assert str(error) == expected_message
