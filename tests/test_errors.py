"""Tests for error and warning message generation."""

import pytest
import os
from typing import List, NamedTuple, Optional

from decoy.spy_events import SpyCall, SpyEvent, SpyInfo, VerifyRehearsal
from decoy.errors import VerifyError


class VerifyErrorSpec(NamedTuple):
    """Spec data for VerifyError tests."""

    rehearsals: List[VerifyRehearsal]
    calls: List[SpyEvent]
    times: Optional[int]
    expected_message: str


verify_error_specs = [
    VerifyErrorSpec(
        rehearsals=[
            VerifyRehearsal(
                spy=SpyInfo(id=42, name="my_spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
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
            VerifyRehearsal(
                spy=SpyInfo(id=42, name="my_spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
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
            VerifyRehearsal(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=202, name="spy_202", is_async=False),
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=202, name="spy_202", is_async=False),
                payload=SpyCall(args=("oh no",), kwargs={}),
            ),
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
            VerifyRehearsal(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
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
    VerifyErrorSpec(
        rehearsals=[
            VerifyRehearsal(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy=SpyInfo(id=101, name="spy_101", is_async=False),
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
        ],
        times=1,
        expected_message=os.linesep.join(
            [
                "Expected exactly 1 call:",
                "1.\tspy_101(1, 2, 3)",
                "Found 1 call:",
                "1.\tspy_101(4, 5, 6)",
            ]
        ),
    ),
]


@pytest.mark.parametrize(VerifyErrorSpec._fields, verify_error_specs)
def test_verify_error(
    rehearsals: List[VerifyRehearsal],
    calls: List[SpyEvent],
    times: Optional[int],
    expected_message: str,
) -> None:
    """It should stringify VerifyError properly."""
    error = VerifyError(rehearsals=rehearsals, calls=calls, times=times)
    assert str(error) == expected_message
