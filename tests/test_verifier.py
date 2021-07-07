"""Tests for spy call verification."""
import pytest
from typing import Any, List, NamedTuple, Optional

from decoy.call_stack import SpyCall, SpyRehearsal
from decoy.errors import VerifyError
from decoy.warnings import MiscalledStubWarning
from decoy.verifier import Verifier


class VerifySpec(NamedTuple):
    """Spec data for verifier.verify tests."""

    rehearsals: List[SpyRehearsal]
    calls: List[SpyCall]
    times: Optional[int] = None


verify_raise_specs = [
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        ],
        calls=[],
    ),
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=42, spy_name="my_spy", args=(), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
        ],
    ),
    VerifySpec(
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
    ),
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        times=1,
    ),
]

verify_pass_specs = [
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=42, spy_name="my_spy", args=(1, 2, 3), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=42, spy_name="my_spy", args=(1, 2, 3), kwargs={}),
        ],
    ),
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
            SpyRehearsal(spy_id=202, spy_name="spy_202", args=(7, 8, 9), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(4, 5, 6), kwargs={}),
            SpyCall(spy_id=202, spy_name="spy_202", args=(7, 8, 9), kwargs={}),
        ],
    ),
    VerifySpec(
        rehearsals=[
            SpyRehearsal(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        calls=[
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
            SpyCall(spy_id=101, spy_name="spy_101", args=(1, 2, 3), kwargs={}),
        ],
        times=2,
    ),
]


@pytest.mark.parametrize(VerifySpec._fields, verify_raise_specs)
def test_verify_raises(
    rehearsals: List[SpyRehearsal],
    calls: List[SpyCall],
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
    rehearsals: List[SpyRehearsal],
    calls: List[SpyCall],
    times: Optional[int],
) -> None:
    """It should no-op if the calls match the rehearsals."""
    subject = Verifier()
    subject.verify(rehearsals=rehearsals, calls=calls, times=times)


class MiscalledStubTestCase(NamedTuple):
    """Spec data for MiscalledStubWarning tests."""

    all_calls: List[SpyCall]
    expected_warnings: List[MiscalledStubWarning]


miscalled_stub_warn_specs = [
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={})],
                calls=[SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={})],
            )
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyRehearsal(spy_id=1, spy_name="spy", args=(0,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(0,), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                ],
            )
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=2, spy_name="yps", args=(2,), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                ],
            )
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyRehearsal(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                ],
            )
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyRehearsal(spy_id=2, spy_name="yps", args=(1,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=2, spy_name="yps", args=(), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                ],
            ),
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=2, spy_name="yps", args=(1,), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=2, spy_name="yps", args=(), kwargs={}),
                ],
            ),
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(2,), kwargs={}),
            SpyRehearsal(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(3,), kwargs={}),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                    SpyCall(spy_id=1, spy_name="spy", args=(2,), kwargs={}),
                ],
            ),
            MiscalledStubWarning(
                rehearsals=[
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(), kwargs={}),
                    SpyRehearsal(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
                ],
                calls=[
                    SpyCall(spy_id=1, spy_name="spy", args=(3,), kwargs={}),
                ],
            ),
        ],
    ),
    MiscalledStubTestCase(
        all_calls=[],
        expected_warnings=[],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyRehearsal(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
        expected_warnings=[],
    ),
    MiscalledStubTestCase(
        all_calls=[
            SpyCall(spy_id=1, spy_name="spy", args=(1,), kwargs={}),
        ],
        expected_warnings=[],
    ),
]


@pytest.mark.parametrize(MiscalledStubTestCase._fields, miscalled_stub_warn_specs)
def test_verify_no_misscalled_stubs(
    all_calls: List[SpyCall],
    expected_warnings: List[MiscalledStubWarning],
    recwarn: pytest.WarningsRecorder,
) -> None:
    """It should parse the list of all calls to find miscalled stubs."""
    subject = Verifier()
    subject.verify_no_miscalled_stubs(all_calls)

    assert len(recwarn) == len(expected_warnings)
    for expected in expected_warnings:
        result: Any = recwarn.pop(MiscalledStubWarning).message
        assert result.rehearsals == expected.rehearsals
        assert result.calls == expected.calls
