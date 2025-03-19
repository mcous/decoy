"""Tests for the WarningChecker API."""

import pytest
from typing import List, NamedTuple, Sequence

from decoy import matchers
from decoy.spy_events import (
    AnySpyEvent,
    SpyCall,
    SpyEvent,
    SpyInfo,
    SpyPropAccess,
    PropAccessType,
    WhenRehearsal,
    VerifyRehearsal,
)
from decoy.warnings import DecoyWarning, MiscalledStubWarning, RedundantVerifyWarning
from decoy.warning_checker import WarningChecker


class WarningCheckerSpec(NamedTuple):
    """Spec data for MiscalledStubWarning tests."""

    all_calls: Sequence[AnySpyEvent]
    expected_warnings: Sequence[DecoyWarning]


warning_checker_specs = [
    # it should not warn if there are no calls
    WarningCheckerSpec(
        all_calls=[],
        expected_warnings=[],
    ),
    # it should not warn if rehearsals and calls match
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[],
    ),
    # it should not warn if a call is made and there are no rehearsals
    WarningCheckerSpec(
        all_calls=[
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[],
    ),
    # it should warn if a spy has a rehearsal and a call that doesn't match
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    )
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    )
                ],
            )
        ],
    ),
    # it should not warn if a spy's verify rehearsal doesn't match
    WarningCheckerSpec(
        all_calls=[
            VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[],
    ),
    # it should not warn due to spy prop access
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyPropAccess(
                    prop_name="prop_name", access_type=PropAccessType.GET
                ),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyPropAccess(
                    prop_name="other_prop", access_type=PropAccessType.GET
                ),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=2, name="spy.other_prop", is_async=False),
                payload=SpyCall(args=(), kwargs={}, ignore_extra_args=False),
            ),
        ],
        expected_warnings=[],
    ),
    # it should warn if a spy has multiple rehearsals without a matching call
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(0,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(0,), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
            )
        ],
    ),
    # it should ignore spies that don't need warnings
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=2, name="yps", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
            )
        ],
    ),
    # it should ignore rehearsals that come after a given call
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
            )
        ],
    ),
    # it should issue multiple warnings for multiple spies
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=2, name="yps", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=2, name="yps", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
            ),
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=2, name="yps", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=2, name="yps", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                ],
            ),
        ],
    ),
    # it should issue multiple warnings for multiple calls to the same spy
    # if the rehearsal list changes
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(3,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(2,), kwargs={}),
                    ),
                ],
            ),
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(), kwargs={}),
                    ),
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(3,), kwargs={}),
                    ),
                ],
            ),
        ],
    ),
    # it should not warn if a call misses a stubbing but is later verified
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
        ],
        expected_warnings=[],
    ),
    # it should warn if a call misses a stubbing after it is verified
    WarningCheckerSpec(
        all_calls=[
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            SpyEvent(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
        ],
        expected_warnings=[
            MiscalledStubWarning(
                rehearsals=[
                    WhenRehearsal(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(1,), kwargs={}),
                    ),
                ],
                calls=[
                    SpyEvent(
                        spy=SpyInfo(id=1, name="spy", is_async=False),
                        payload=SpyCall(args=(2,), kwargs={}),
                    ),
                ],
            ),
        ],
    ),
    # it should issue a redundant verify warning if a call has a when and a verify
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
        ],
        expected_warnings=[
            RedundantVerifyWarning(
                rehearsal=VerifyRehearsal(
                    spy=SpyInfo(id=1, name="spy", is_async=False),
                    payload=SpyCall(
                        args=(1,),
                        kwargs={},
                    ),
                ),
            ),
        ],
    ),
    # it should not warn if the verify and when rehearsals are different
    WarningCheckerSpec(
        all_calls=[
            WhenRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(1,), kwargs={}),
            ),
            VerifyRehearsal(
                spy=SpyInfo(id=1, name="spy", is_async=False),
                payload=SpyCall(args=(2,), kwargs={}),
            ),
        ],
        expected_warnings=[],
    ),
]


@pytest.mark.parametrize(WarningCheckerSpec._fields, warning_checker_specs)
def test_verify_no_misscalled_stubs(
    all_calls: List[SpyEvent],
    expected_warnings: List[MiscalledStubWarning],
    recwarn: pytest.WarningsRecorder,
) -> None:
    """It should parse the list of all calls to find miscalled stubs."""
    subject = WarningChecker()
    subject.check(all_calls)

    warning_matchers = []

    for warning in expected_warnings:
        if isinstance(warning, MiscalledStubWarning):
            warning_attr = {"rehearsals": warning.rehearsals, "calls": warning.calls}
        elif isinstance(warning, RedundantVerifyWarning):
            warning_attr = {"rehearsal": warning.rehearsal}

        warning_matchers.append(matchers.IsA(type(warning), warning_attr))

    actual_warnings = [record.message for record in recwarn]

    assert actual_warnings == warning_matchers
