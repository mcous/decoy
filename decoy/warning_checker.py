"""Warning checker."""

from collections import defaultdict
from itertools import groupby
from typing import Dict, List, NamedTuple, Sequence
from warnings import warn

from .spy_events import (
    AnySpyEvent,
    SpyCall,
    SpyEvent,
    SpyRehearsal,
    VerifyRehearsal,
    WhenRehearsal,
    match_event,
)
from .warnings import DecoyWarning, MiscalledStubWarning, RedundantVerifyWarning


class WarningChecker:
    """An interface to inspect the call list and trigger any necessary warnings."""

    @staticmethod
    def check(all_calls: Sequence[AnySpyEvent]) -> None:
        """Check full call and rehearsal list for any potential misuse."""
        _check_no_miscalled_stubs(all_calls)
        _check_no_redundant_verify(all_calls)


class _Call(NamedTuple):
    event: SpyEvent
    all_rehearsals: List[SpyRehearsal]
    matching_rehearsals: List[SpyRehearsal]


def _check_no_miscalled_stubs(all_events: Sequence[AnySpyEvent]) -> None:
    """Ensure every call matches a rehearsal, if the spy has rehearsals."""
    all_events_by_id: Dict[int, List[AnySpyEvent]] = defaultdict(list)
    all_calls_by_id: Dict[int, List[_Call]] = defaultdict(list)

    for event in all_events:
        all_events_by_id[event.spy.id].append(event)

    for events in all_events_by_id.values():
        for index, event in enumerate(events):
            if isinstance(event, SpyEvent) and isinstance(event.payload, SpyCall):
                when_rehearsals = [
                    rehearsal
                    for rehearsal in events[0:index]
                    if isinstance(rehearsal, WhenRehearsal)
                    and isinstance(rehearsal.payload, SpyCall)
                ]
                verify_rehearsals = [
                    rehearsal
                    for rehearsal in events[index + 1 :]
                    if isinstance(rehearsal, VerifyRehearsal)
                    and isinstance(rehearsal.payload, SpyCall)
                ]

                all_rehearsals: List[SpyRehearsal] = [
                    *when_rehearsals,
                    *verify_rehearsals,
                ]
                matching_rehearsals = [
                    rehearsal
                    for rehearsal in all_rehearsals
                    if match_event(event, rehearsal)
                ]

                all_calls_by_id[event.spy.id].append(
                    _Call(event, all_rehearsals, matching_rehearsals)
                )

    for spy_calls in all_calls_by_id.values():
        for rehearsals, grouped_calls in groupby(spy_calls, lambda c: c.all_rehearsals):
            calls = list(grouped_calls)
            is_stubbed = any(isinstance(r, WhenRehearsal) for r in rehearsals)

            if is_stubbed and all(len(c.matching_rehearsals) == 0 for c in calls):
                _warn(
                    MiscalledStubWarning.create(
                        calls=[c.event for c in calls],
                        rehearsals=rehearsals,
                    )
                )


def _check_no_redundant_verify(all_calls: Sequence[AnySpyEvent]) -> None:
    when_rehearsals = [c for c in all_calls if isinstance(c, WhenRehearsal)]
    verify_rehearsals = [c for c in all_calls if isinstance(c, VerifyRehearsal)]

    for vr in verify_rehearsals:
        if any(wr for wr in when_rehearsals if wr == vr):  # type: ignore[comparison-overlap]
            _warn(RedundantVerifyWarning.create(rehearsal=vr))


def _warn(warning: DecoyWarning) -> None:
    """Trigger a warning, at the stack level of whatever called `Decoy.reset`."""
    warn(warning, stacklevel=6)
