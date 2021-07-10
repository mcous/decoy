"""Warning checker."""
from typing import Dict, List, Sequence
from warnings import warn

from .spy_calls import BaseSpyCall, SpyCall, WhenRehearsal, VerifyRehearsal
from .warnings import MiscalledStubWarning, RedundantVerifyWarning


class WarningChecker:
    """An interface to inspect the call list and trigger any necessary warnings."""

    @staticmethod
    def check(all_calls: Sequence[BaseSpyCall]) -> None:
        """Check full call and rehearsal list for any potential misuse."""
        _check_no_miscalled_stubs(all_calls)
        _check_no_redundant_verify(all_calls)


def _check_no_miscalled_stubs(all_calls: Sequence[BaseSpyCall]) -> None:
    """Ensure every call matches a rehearsal, if the spy has rehearsals."""
    all_calls_by_id: Dict[int, List[BaseSpyCall]] = {}

    for call in all_calls:
        spy_id = call.spy_id
        spy_calls = all_calls_by_id.get(spy_id, [])
        all_calls_by_id[spy_id] = spy_calls + [call]

    for spy_id, spy_calls in all_calls_by_id.items():
        rehearsals: List[WhenRehearsal] = []
        unmatched: List[SpyCall] = []

        for call in spy_calls:
            next_rehearsals = rehearsals
            next_unmatched = unmatched

            if isinstance(call, WhenRehearsal):
                next_rehearsals = rehearsals + [call]

                if len(unmatched) > 0:
                    next_unmatched = []

                    warn(
                        MiscalledStubWarning(
                            calls=unmatched,
                            rehearsals=rehearsals,
                        )
                    )
            elif (
                isinstance(call, SpyCall)
                and len(rehearsals) > 0
                and not any(rh == call for rh in rehearsals)
            ):
                next_unmatched = unmatched + [call]

            rehearsals = next_rehearsals
            unmatched = next_unmatched

        if len(unmatched) > 0:
            warn(MiscalledStubWarning(calls=unmatched, rehearsals=rehearsals))


def _check_no_redundant_verify(all_calls: Sequence[BaseSpyCall]) -> None:
    when_rehearsals = [c for c in all_calls if isinstance(c, WhenRehearsal)]
    verify_rehearsals = [c for c in all_calls if isinstance(c, VerifyRehearsal)]

    for vr in verify_rehearsals:
        if any(wr for wr in when_rehearsals if wr == vr):
            warn(RedundantVerifyWarning(rehearsal=vr))
