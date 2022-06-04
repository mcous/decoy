"""Warning checker."""
from typing import Dict, List, Sequence
from warnings import warn

from .spy_events import (
    AnySpyEvent,
    SpyCall,
    SpyEvent,
    VerifyRehearsal,
    WhenRehearsal,
    match_event,
)
from .warnings import MiscalledStubWarning, RedundantVerifyWarning


class WarningChecker:
    """An interface to inspect the call list and trigger any necessary warnings."""

    @staticmethod
    def check(all_calls: Sequence[AnySpyEvent]) -> None:
        """Check full call and rehearsal list for any potential misuse."""
        _check_no_miscalled_stubs(all_calls)
        _check_no_redundant_verify(all_calls)


def _check_no_miscalled_stubs(all_events: Sequence[AnySpyEvent]) -> None:
    """Ensure every call matches a rehearsal, if the spy has rehearsals."""
    all_calls_by_id: Dict[int, List[AnySpyEvent]] = {}

    for event in all_events:
        if isinstance(event.payload, SpyCall):
            spy_id = event.spy.id
            spy_calls = all_calls_by_id.get(spy_id, [])
            all_calls_by_id[spy_id] = spy_calls + [event]

    for spy_calls in all_calls_by_id.values():
        unmatched: List[SpyEvent] = []

        for index, call in enumerate(spy_calls):
            past_stubs = [
                wr for wr in spy_calls[0:index] if isinstance(wr, WhenRehearsal)
            ]

            matched_past_stubs = [wr for wr in past_stubs if match_event(call, wr)]

            matched_future_verifies = [
                vr
                for vr in spy_calls[index + 1 :]
                if isinstance(vr, VerifyRehearsal) and match_event(call, vr)
            ]

            if (
                isinstance(call, SpyEvent)
                and len(past_stubs) > 0
                and len(matched_past_stubs) == 0
                and len(matched_future_verifies) == 0
            ):
                unmatched = unmatched + [call]
                if index == len(spy_calls) - 1:
                    warn(MiscalledStubWarning(calls=unmatched, rehearsals=past_stubs))
            elif isinstance(call, WhenRehearsal) and len(unmatched) > 0:
                warn(MiscalledStubWarning(calls=unmatched, rehearsals=past_stubs))
                unmatched = []


def _check_no_redundant_verify(all_calls: Sequence[AnySpyEvent]) -> None:
    when_rehearsals = [c for c in all_calls if isinstance(c, WhenRehearsal)]
    verify_rehearsals = [c for c in all_calls if isinstance(c, VerifyRehearsal)]

    for vr in verify_rehearsals:
        if any(wr for wr in when_rehearsals if wr == vr):
            warn(RedundantVerifyWarning(rehearsal=vr))
