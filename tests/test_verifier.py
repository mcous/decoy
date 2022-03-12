"""Tests for spy call verification."""
import pytest
from typing import List, NamedTuple, Optional

from decoy.spy_events import SpyCall, SpyEvent, VerifyRehearsal
from decoy.errors import VerifyError
from decoy.verifier import Verifier


class VerifySpec(NamedTuple):
    """Spec data for verifier.verify tests."""

    rehearsals: List[VerifyRehearsal]
    calls: List[SpyEvent]
    times: Optional[int] = None


verify_raise_specs = [
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=42, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
            ),
        ],
        calls=[],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=42, spy_name="my_spy", payload=SpyCall(args=(), kwargs={})
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            SpyEvent(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=("oh no",), kwargs={}),
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        times=1,
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        times=0,
    ),
]

verify_pass_specs = [
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=42, spy_name="my_spy", payload=SpyCall(args=(1, 2, 3), kwargs={})
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=42, spy_name="my_spy", payload=SpyCall(args=(1, 2, 3), kwargs={})
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            SpyEvent(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            VerifyRehearsal(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(0, 0, 0), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            SpyEvent(
                spy_id=202,
                spy_name="spy_202",
                payload=SpyCall(args=(7, 8, 9), kwargs={}),
            ),
        ],
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        times=2,
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(4, 5, 6), kwargs={}),
            ),
            SpyEvent(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        times=1,
    ),
    VerifySpec(
        rehearsals=[
            VerifyRehearsal(
                spy_id=101,
                spy_name="spy_101",
                payload=SpyCall(args=(1, 2, 3), kwargs={}),
            ),
        ],
        calls=[],
        times=0,
    ),
]


@pytest.mark.parametrize(VerifySpec._fields, verify_raise_specs)
def test_verify_raises(
    rehearsals: List[VerifyRehearsal],
    calls: List[SpyEvent],
    times: Optional[int],
) -> None:
    """It should raise an error if calls do not match rehearsals."""
    subject = Verifier()

    with pytest.raises(VerifyError) as error_info:
        subject.verify(rehearsals=rehearsals, calls=calls, times=times)

    assert error_info.value.calls == calls
    assert error_info.value.rehearsals == rehearsals
    assert error_info.value.times == times


@pytest.mark.parametrize(VerifySpec._fields, verify_pass_specs)
def test_verify_passes(
    rehearsals: List[VerifyRehearsal],
    calls: List[SpyEvent],
    times: Optional[int],
) -> None:
    """It should no-op if the calls match the rehearsals."""
    subject = Verifier()
    subject.verify(rehearsals=rehearsals, calls=calls, times=times)
