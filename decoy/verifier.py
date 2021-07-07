"""Spy call verification."""
from typing import Dict, List, Optional, Sequence
from warnings import warn

from .call_stack import SpyCall, SpyRehearsal
from .errors import VerifyError
from .warnings import MiscalledStubWarning


class Verifier:
    """An interface to verify that spies were called as expected."""

    @staticmethod
    def verify(
        rehearsals: Sequence[SpyRehearsal],
        calls: Sequence[SpyCall],
        times: Optional[int] = None,
    ) -> None:
        """Verify that a list of calls satisfies a given list of rehearsals."""
        if times is not None:
            if len(calls) == times:
                return None
        else:
            for i, call in enumerate(calls):
                calls_subset = calls[i : i + len(rehearsals)]
                if all(r == calls_subset[j] for j, r in enumerate(rehearsals)):
                    return None

        raise VerifyError(
            rehearsals=rehearsals,
            calls=calls,
            times=times,
        )

    @staticmethod
    def verify_no_miscalled_stubs(all_calls: Sequence[SpyCall]) -> None:
        """Ensure every call matches a rehearsal, if the spy has rehearsals."""
        all_calls_by_id: Dict[int, List[SpyCall]] = {}

        for call in all_calls:
            spy_id = call.spy_id
            spy_calls = all_calls_by_id.get(spy_id, [])
            all_calls_by_id[spy_id] = spy_calls + [call]

        for spy_id, spy_calls in all_calls_by_id.items():
            rehearsals: List[SpyRehearsal] = []
            unmatched: List[SpyCall] = []

            for call in spy_calls:
                next_rehearsals = rehearsals
                next_unmatched = unmatched

                if isinstance(call, SpyRehearsal):
                    next_rehearsals = rehearsals + [call]

                    if len(unmatched) > 0:
                        next_unmatched = []

                        warn(
                            MiscalledStubWarning(
                                calls=unmatched,
                                rehearsals=rehearsals,
                            )
                        )
                elif len(rehearsals) > 0 and not any(rh == call for rh in rehearsals):
                    next_unmatched = unmatched + [call]

                rehearsals = next_rehearsals
                unmatched = next_unmatched

            if len(unmatched) > 0:
                warn(MiscalledStubWarning(calls=unmatched, rehearsals=rehearsals))
